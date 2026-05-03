# Hermex

ChatGPT and Gemini are incredibly capable — but their official APIs are expensive, and for many tasks you simply don't need them. If you want to run OCR on an image, generate artwork, extract text from a screenshot, or just ask a quick question in a script, paying per-token for API access is overkill when the free web UI can do the same thing.

Hermex lets you drive ChatGPT and Gemini from Python just like a human would: it opens a real Chrome browser, types your message, uploads your images, waits for the response, and hands it back to you as a Python object. No API keys, no billing, no rate-limit tiers.

```python
from hermex import ChatGPT

response = ChatGPT.simple_query("What does this receipt say?", images=["receipt.jpg"])
print(response.text)
```

## Why Hermex?

- **No API keys** — uses the same free web UI you already have access to
- **Image support** — upload images and download AI-generated ones
- **Bot detection evasion** — built on `undetected-chromedriver` with simulated human typing
- **Persistent sessions** — log in once, reuse the session across all future runs
- **Fluent interface** — chain method calls for clean, readable scripts

## Get started

[Installation](installation.md){ .md-button .md-button--primary }
[Quickstart](quickstart.md){ .md-button }
