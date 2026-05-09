# Gemini

`Gemini` targets [gemini.google.com](https://gemini.google.com). All methods shared with `ChatGPT` are documented on the [Shared Interface](shared-interface.md) page — this page covers only what is specific to Gemini.

---

## Guest mode vs logged-in mode

Gemini works in two modes depending on whether you are logged in:

| Feature | Guest mode | Logged in |
|---|---|---|
| Text queries | ✓ | ✓ |
| File upload | ✗ | ✓ |
| Generated image download | ✓ | ✓ |
| Watermark removal | ✓ | ✓ |

Attempting file upload without a logged-in session raises [`LoginRequiredError`](exceptions.md). Run `Gemini.setup()` and log in to enable it.

---

## Supported attachments

`Gemini.SUPPORTED_ATTACHMENTS` is the set of file extensions accepted for upload. Passing any other extension to `send_message()` or `query()` raises a `ValueError` before touching the browser.

```python
print(Gemini.SUPPORTED_ATTACHMENTS)
# {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.pdf', '.csv', '.txt', '.json'}
```

::: hermex.gemini.Gemini
    options:
      members:
        - SUPPORTED_ATTACHMENTS

---

## Watermark removal

Gemini watermarks its generated images. Pass `remove_watermark=True` to `query()` or `get_last_response()` to strip it automatically using OpenCV template matching — no external service involved.

```python
response = gemini.query("Generate an image of a sunset.", remove_watermark=True)
```

---

## Default URL

`open_url()` defaults to `https://gemini.google.com` and raises `ValueError` if a non-Gemini URL is passed.
