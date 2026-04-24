---
name: wecom-notify
description: Send Enterprise WeChat or WeCom group robot notifications from Codex automations by reading webhook configuration from .env.dev. Use when Codex needs to notify a configured chat after code review, pull request creation, CI or automation completion, or when asking responsible people to optimize code; never hardcode webhook keys or URLs in prompts, code, commits, logs, or skill files.
---

# WeCom Notify

## Overview

Send concise Enterprise WeChat notifications from Codex workflows without exposing robot credentials. Use the bundled curl script so webhook keys stay in `.env.dev` and message payloads are built consistently.

## Configuration

Read configuration from `.env.dev`, searching from the current working directory upward unless an explicit env file is provided.

Prefer one of these variables:

```dotenv
WECOM_WEBHOOK_KEY=replace-with-the-key-query-value
# or
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=replace-with-key
```

Also accepted for compatibility: `WECHAT_WORK_WEBHOOK_KEY`, `WECHAT_WORK_WEBHOOK_URL`, `QYWX_WEBHOOK_KEY`, `QYWX_WEBHOOK_URL`, `ENTERPRISE_WECHAT_WEBHOOK_KEY`, `ENTERPRISE_WECHAT_WEBHOOK_URL`, `WECHAT_NOTIFY_ID`, `WECOM_NOTIFY_ID`.

Do not print, commit, paste, or summarize the webhook key. If the key is missing, tell the user to add it to `.env.dev`.

If macOS blocks reading a project under `~/Documents`, either grant Codex access to the Documents folder or inject `WECOM_WEBHOOK_KEY` / `WECOM_WEBHOOK_URL` into the automation environment; the script can send from environment variables without reading `.env.dev`.

## Quick Send

Use `.codex/skills/wecom-notify/scripts/send_wecom.sh` from the repository root for automation-safe sending:

```bash
bash .codex/skills/wecom-notify/scripts/send_wecom.sh \
  --env-file /path/to/project/.env.dev \
  --type markdown \
  --content "## CodeReview 完成\n> 请查看最新结论。"
```

To avoid leaking sensitive data during validation, run dry-run first:

```bash
bash .codex/skills/wecom-notify/scripts/send_wecom.sh \
  --env-file /path/to/project/.env.dev \
  --type text \
  --content "dry run" \
  --dry-run
```

The script supports `text`, `markdown`, and `markdown_v2`. It accepts `--content`, `--content-file`, or stdin. It requires `curl` and `jq`, both available on macOS in this workspace.

## Message Style

Keep automation notifications short and actionable:

- Start with a clear event title, such as `CodeReview 完成`, `PR 已创建`, or `需要优化代码`.
- Include repository/module, branch or PR link, status, and next action.
- Prefer `markdown` when a PR URL, findings summary, or responsible party list is included.
- Use `--mentioned-list` or `--mentioned-mobile-list` only for urgent or directly assigned work; `@all` should be rare.
- Stay under WeCom limits: text content up to 2048 bytes, markdown content up to 4096 bytes, and no more than 20 robot messages per minute.

Example markdown body:

```markdown
## PR 已创建
> 仓库: bk-lite
> 分支: codex/example
> 状态: 等待 Review

[打开 PR](https://example.com/pr/1)
```

## References

Read `references/wecom-webhook.md` only when you need payload details, message limits, or supported message type notes.
