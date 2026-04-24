#!/usr/bin/env bash
set -euo pipefail

WEBHOOK_BASE_URL="https://qyapi.weixin.qq.com/cgi-bin/webhook/send"
KEY_NAMES=(
  WECOM_WEBHOOK_KEY
  WECHAT_WORK_WEBHOOK_KEY
  QYWX_WEBHOOK_KEY
  ENTERPRISE_WECHAT_WEBHOOK_KEY
  WECHAT_NOTIFY_ID
  WECOM_NOTIFY_ID
)
URL_NAMES=(
  WECOM_WEBHOOK_URL
  WECHAT_WORK_WEBHOOK_URL
  QYWX_WEBHOOK_URL
  ENTERPRISE_WECHAT_WEBHOOK_URL
)

ENV_FILE=""
MSGTYPE="markdown"
CONTENT=""
CONTENT_FILE=""
MENTIONED_LIST=""
MENTIONED_MOBILE_LIST=""
DRY_RUN=0
TIMEOUT=10

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

usage() {
  cat <<'USAGE'
Usage: send_wecom.sh [options]

Options:
  --env-file PATH                 Path to .env.dev; defaults to searching cwd and parents
  --type text|markdown|markdown_v2 WeCom message type, default: markdown
  --content TEXT                  Message content
  --content-file PATH             UTF-8 file containing message content
  --mentioned-list IDS            Comma-separated user IDs for text messages
  --mentioned-mobile-list PHONES  Comma-separated mobile numbers for text messages
  --dry-run                       Validate and print redacted payload without sending
  --timeout SECONDS               curl timeout, default: 10
  -h, --help                      Show this help
USAGE
}

trim() {
  printf '%s' "$1" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'
}

strip_quotes() {
  local value="$1"
  local first="${value:0:1}"
  local last="${value: -1}"
  if [[ ${#value} -ge 2 && ( "$first" == "'" || "$first" == '"' ) && "$first" == "$last" ]]; then
    printf '%s' "${value:1:${#value}-2}"
  else
    printf '%s' "$value"
  fi
}

find_env_file() {
  if [[ -n "$ENV_FILE" ]]; then
    printf '%s\n' "$ENV_FILE"
    return
  fi

  local dir
  dir="$(pwd -P)"
  while :; do
    if [[ -f "$dir/.env.dev" ]]; then
      printf '%s\n' "$dir/.env.dev"
      return
    fi
    [[ "$dir" == "/" ]] && break
    dir="$(dirname "$dir")"
  done

  printf '%s\n' "$(pwd -P)/.env.dev"
}

load_env_file() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    if has_webhook_env; then
      return
    fi
    die "env file not found: $file"
  fi

  if ! : < "$file" 2>/dev/null; then
    if has_webhook_env; then
      return
    fi
    die "env file is not readable: $file. On macOS, grant Codex access to Documents or export WECOM_WEBHOOK_KEY/WECOM_WEBHOOK_URL in the automation environment."
  fi

  local line key value
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="$(trim "$line")"
    [[ -z "$line" || "${line:0:1}" == "#" ]] && continue
    [[ "$line" == export\ * ]] && line="$(trim "${line#export }")"
    [[ "$line" == *"="* ]] || continue
    key="$(trim "${line%%=*}")"
    value="$(trim "${line#*=}")"
    [[ -n "$key" ]] || continue
    value="$(strip_quotes "$value")"
    export "$key=$value"
  done < "$file"
}

first_env_value() {
  local name value
  for name in "$@"; do
    value="${!name-}"
    if [[ -n "$value" ]]; then
      printf '%s\n' "$value"
      return 0
    fi
  done
  return 1
}

has_webhook_env() {
  first_env_value "${URL_NAMES[@]}" >/dev/null 2>&1 || first_env_value "${KEY_NAMES[@]}" >/dev/null 2>&1
}

webhook_url() {
  local value encoded
  if value="$(first_env_value "${URL_NAMES[@]}")"; then
    printf '%s\n' "$value"
    return
  fi

  if value="$(first_env_value "${KEY_NAMES[@]}")"; then
    if [[ "$value" == http://* || "$value" == https://* ]]; then
      printf '%s\n' "$value"
      return
    fi
    encoded="$(printf '%s' "$value" | jq -sRr @uri)"
    printf '%s?key=%s\n' "$WEBHOOK_BASE_URL" "$encoded"
    return
  fi

  die "missing WeCom webhook config; set WECOM_WEBHOOK_KEY or WECOM_WEBHOOK_URL in .env.dev"
}

redact_url() {
  printf '%s' "$1" | sed -E 's/([?&]key=)[^&]*/\1***/g'
}

read_content() {
  [[ -n "$CONTENT" && -n "$CONTENT_FILE" ]] && die "provide only one content source: --content or --content-file"
  if [[ -n "$CONTENT" ]]; then
    printf '%s' "$CONTENT"
  elif [[ -n "$CONTENT_FILE" ]]; then
    [[ -f "$CONTENT_FILE" ]] || die "content file not found: $CONTENT_FILE"
    cat "$CONTENT_FILE"
  else
    cat
  fi
}

byte_len() {
  LC_ALL=C printf '%s' "$1" | wc -c | tr -d ' '
}

csv_json() {
  if [[ -z "$1" ]]; then
    printf '[]'
  else
    printf '%s' "$1" | jq -R 'split(",") | map(gsub("^\\s+|\\s+$"; "")) | map(select(length > 0))'
  fi
}

build_payload() {
  local content="$1"
  case "$MSGTYPE" in
    text)
      local mentioned mentioned_mobile
      mentioned="$(csv_json "$MENTIONED_LIST")"
      mentioned_mobile="$(csv_json "$MENTIONED_MOBILE_LIST")"
      jq -n \
        --arg content "$content" \
        --argjson mentioned "$mentioned" \
        --argjson mentioned_mobile "$mentioned_mobile" '
        {
          msgtype: "text",
          text: (
            {content: $content}
            + (if ($mentioned | length) > 0 then {mentioned_list: $mentioned} else {} end)
            + (if ($mentioned_mobile | length) > 0 then {mentioned_mobile_list: $mentioned_mobile} else {} end)
          )
        }'
      ;;
    markdown)
      jq -n --arg content "$content" '{msgtype: "markdown", markdown: {content: $content}}'
      ;;
    markdown_v2)
      jq -n --arg content "$content" '{msgtype: "markdown_v2", markdown_v2: {content: $content}}'
      ;;
    *)
      die "unsupported message type: $MSGTYPE"
      ;;
  esac
}

post_payload() {
  local url="$1"
  local payload="$2"
  local response http_code errcode errmsg
  response="$(mktemp)"
  http_code="$(
    curl -sS \
      --max-time "$TIMEOUT" \
      -o "$response" \
      -w '%{http_code}' \
      -H 'Content-Type: application/json' \
      -d "$payload" \
      "$url"
  )" || {
    rm -f "$response"
    die "curl request failed"
  }

  if [[ "$http_code" != 2* ]]; then
    local body
    body="$(cat "$response")"
    rm -f "$response"
    die "WeCom HTTP $http_code: $body"
  fi

  errcode="$(jq -r '.errcode // empty' "$response")"
  errmsg="$(jq -r '.errmsg // empty' "$response")"
  rm -f "$response"
  [[ "$errcode" == "0" ]] || die "WeCom API error ${errcode:-unknown}: ${errmsg:-unknown error}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      ENV_FILE="${2:-}"
      shift 2
      ;;
    --type)
      MSGTYPE="${2:-}"
      shift 2
      ;;
    --content)
      CONTENT="${2:-}"
      shift 2
      ;;
    --content-file)
      CONTENT_FILE="${2:-}"
      shift 2
      ;;
    --mentioned-list)
      MENTIONED_LIST="${2:-}"
      shift 2
      ;;
    --mentioned-mobile-list)
      MENTIONED_MOBILE_LIST="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --timeout)
      TIMEOUT="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown option: $1"
      ;;
  esac
done

command -v curl >/dev/null 2>&1 || die "curl is required"
command -v jq >/dev/null 2>&1 || die "jq is required"

ENV_FILE="$(find_env_file)"
load_env_file "$ENV_FILE"

URL="$(webhook_url)"
MESSAGE_CONTENT="$(read_content)"
[[ -n "$(trim "$MESSAGE_CONTENT")" ]] || die "content cannot be empty"

LIMIT=4096
[[ "$MSGTYPE" == "text" ]] && LIMIT=2048
SIZE="$(byte_len "$MESSAGE_CONTENT")"
[[ "$SIZE" -le "$LIMIT" ]] || die "$MSGTYPE content is $SIZE bytes; limit is $LIMIT bytes"

PAYLOAD="$(build_payload "$MESSAGE_CONTENT")"

if [[ "$DRY_RUN" -eq 1 ]]; then
  printf 'env_file=%s\n' "$ENV_FILE"
  printf 'webhook_url=%s\n' "$(redact_url "$URL")"
  printf '%s\n' "$PAYLOAD"
  exit 0
fi

post_payload "$URL" "$PAYLOAD"
printf 'WeCom notification sent\n'
