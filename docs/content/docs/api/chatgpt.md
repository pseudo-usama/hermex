---
description: API reference for the ChatGPT scraper — supported attachments, login requirements, image generation, and ChatGPT-specific behavior.
---

# ChatGPT

`ChatGPT` targets [chatgpt.com](https://chatgpt.com). All methods shared with `Gemini` are documented on the [Shared Interface](shared-interface.md) page — this page covers only what is specific to ChatGPT.

---

## Login

ChatGPT works without login for text queries only. Signed out, chatgpt.com serves a reduced site that gates both file upload and image generation behind a login — `_upload_files()` raises `LoginRequiredError` there, and image prompts come back as a prompt to log in. Run `ChatGPT.setup()` and log in to enable both. Setup is also recommended regardless for bot detection, as it builds a persistent browser profile.

---

## Supported attachments

`ChatGPT.SUPPORTED_ATTACHMENTS` is the set of file extensions accepted for upload. Passing any other extension to `send_message()` or `query()` raises a `ValueError` before touching the browser.

```python
print(ChatGPT.SUPPORTED_ATTACHMENTS)
# {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.pdf', '.csv', '.txt', '.json'}
```

::: hermex.chatgpt.ChatGPT
    options:
      members:
        - SUPPORTED_ATTACHMENTS

---

## Generated images

ChatGPT does not watermark its generated images. The `remove_watermark` parameter on `query()` and `get_last_response()` is accepted but has no effect.

---

## Default URL

`open_url()` defaults to `https://chatgpt.com` and raises `ValueError` if a non-ChatGPT URL is passed.