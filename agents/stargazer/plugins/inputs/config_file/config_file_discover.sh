#!/bin/bash
FILE_PATH='{{config_file_path}}'

if [ ! -f "$FILE_PATH" ]; then
  printf '{"status":"error","error_type":"file_not_found","error":"文件不存在","size":0}\n'
  exit 0
fi

if [ ! -r "$FILE_PATH" ]; then
  printf '{"status":"error","error_type":"permission_denied","error":"无读取权限","size":0}\n'
  exit 0
fi

FILE_SIZE=$(wc -c < "$FILE_PATH" | tr -d ' ')
if command -v file >/dev/null 2>&1; then
  FILE_TYPE=$(file -b --mime-type "$FILE_PATH" 2>/dev/null || true)
  case "$FILE_TYPE" in
    ''|text/*|application/json|application/xml|application/yaml|application/x-yaml) ;;
    *)
      printf '{"status":"error","error_type":"not_text","error":"非文本文件","size":%s}\n' "$FILE_SIZE"
      exit 0
      ;;
  esac
fi

CONTENT=$(base64 < "$FILE_PATH" | tr -d '\n')
printf '{"status":"success","content_base64":"%s","size":%s}\n' "$CONTENT" "$FILE_SIZE"
