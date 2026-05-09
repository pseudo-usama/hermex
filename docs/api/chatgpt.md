# ChatGPT

`ChatGPT` targets [chatgpt.com](https://chatgpt.com). All methods shared with `Gemini` are documented on the [Shared Interface](shared-interface.md) page — this page covers only what is specific to ChatGPT.

---

## Login

ChatGPT works without login for all features including file upload. You can still run `ChatGPT.setup()` to build a persistent browser profile (recommended for bot detection), but logging in is optional.

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