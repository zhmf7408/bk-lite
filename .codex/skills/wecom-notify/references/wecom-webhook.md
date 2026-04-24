# WeCom Webhook Reference

Use this reference only when payload details are needed.

## Endpoint

Send messages with HTTPS POST:

```text
https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=KEY
```

Keep `KEY` in `.env.dev`; do not commit or echo it.

## Supported Message Types

This skill's script supports the automation-friendly types:

- `text`: plain text, up to 2048 UTF-8 bytes; supports `mentioned_list` and `mentioned_mobile_list`.
- `markdown`: WeCom markdown subset, up to 4096 UTF-8 bytes; supports inline `<@userid>` mentions.
- `markdown_v2`: richer markdown subset, up to 4096 UTF-8 bytes; does not support WeCom font colors or mention extension syntax.

The WeCom robot API also supports image, news, file, voice, and template card payloads. Add script support only when a real automation needs those types.

## Text Payload

```json
{
  "msgtype": "text",
  "text": {
    "content": "message",
    "mentioned_list": ["userid", "@all"],
    "mentioned_mobile_list": ["13800001111"]
  }
}
```

## Markdown Payload

```json
{
  "msgtype": "markdown",
  "markdown": {
    "content": "## 标题\n> 内容\n[链接](https://example.com)"
  }
}
```

Supported markdown subset includes headings, bold, links, inline code, block quotes, and WeCom font colors: `info`, `comment`, `warning`.

## Operational Limits

- One robot webhook can send at most 20 messages per minute.
- Image files are limited to 2 MB before base64 encoding.
- Uploaded files are limited to 20 MB and media IDs are valid for 3 days.
- Uploaded voice files are limited to 2 MB, 60 seconds, and AMR format.
