<p align="center">
  <a href="https://hermex.usama.ai/">
    <img src="https://raw.githubusercontent.com/pseudo-usama/hermex/main/docs/assets/logo.svg" alt="Hermex" width="450" style="margin: 24px 0;"/>
  </a>
  <br>
  <em>Drive ChatGPT and Gemini from Python — no API keys, no billing, just the free web UI.</em>
  <br><br>
  <a href="https://pypi.org/project/hermex">
    <img src="https://img.shields.io/pypi/v/hermex?color=3cb371" alt="PyPI"/>
  </a>
  <a href="https://pypi.org/project/hermex">
    <img src="https://img.shields.io/pypi/pyversions/hermex?color=3cb371" alt="Python 3.11+"/>
  </a>
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT License"/>
  <a href="https://github.com/pseudo-usama/hermex">
    <img src="https://img.shields.io/badge/GitHub-Hermex-181717?logo=github" alt="GitHub Repo"/>
  </a>
  <a href="https://hermex.usama.ai">
    <img src="https://img.shields.io/badge/docs-hermex.usama.ai-3cb371" alt="Docs"/>
  </a>
</p>

---

ChatGPT and Gemini are incredibly capable — but their official APIs are expensive, and for many tasks you simply don't need them. If you want to run OCR on an image, generate artwork, extract text from a screenshot, or just ask a quick question in a script, paying per-token for API access is overkill when the free web UI can do the same thing.

Hermex lets you drive ChatGPT and Gemini from Python just like a human would: it opens a real Chrome browser, types your message, uploads your files, waits for the response, and hands it back to you as a Python object. No API keys, no billing, no rate-limit tiers.

```python
from hermex import ChatGPT

response = ChatGPT.simple_query("What does this receipt say?", attachments=["receipt.jpg"])
print(response.text)
```

It uses undetected-chromedriver under the hood to avoid bot detection, and reuses a persistent browser profile so your login session survives across runs.

## Installation

```bash
pip install hermex
```

Requires Python 3.11+ and Google Chrome 130+.

## First-time setup

Hermex reuses a persistent Chrome profile so you only need to log in once:

```python
from hermex import Gemini

Gemini.setup()  # opens a browser — log in, browse briefly, then close the window
```

After setup, all future runs reuse the saved session automatically. Repeat this if your session expires.

Guest mode (no login) works for basic text queries on Gemini but file upload requires a logged-in session. ChatGPT works without login for text queries and file upload, but image generation requires a logged-in session.

## Usage

### Single query

```python
from hermex import Gemini, ChatGPT

# Gemini
gemini = Gemini()
gemini.open_url()
response = gemini.query("Summarize the history of the internet.")
print(response.text)
gemini.close()

# ChatGPT
chatgpt = ChatGPT()
chatgpt.open_url()
response = chatgpt.query("Summarize the history of the internet.")
print(response.text)
chatgpt.close()
```

### Attaching files

```python
response = gemini.query(
    "Describe what's in this image.",
    attachments=["photo.jpg"],
)
print(response.text)
```

Supported formats: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.pdf`, `.csv`, `.txt`, `.json`. Each platform exposes its allowed types via `Gemini.SUPPORTED_ATTACHMENTS` and `ChatGPT.SUPPORTED_ATTACHMENTS`.

### One-shot query

```python
from hermex import Gemini, ChatGPT

response = Gemini.simple_query("What is the capital of France?")
print(response.text)

response = ChatGPT.simple_query("What is the capital of France?")
print(response.text)

# With an attachment
response = Gemini.simple_query("Describe this image.", attachments=["photo.jpg"])
print(response.text)
```

## AssistantMessage object

`query()` and `get_last_response()` return an `AssistantMessage` dataclass:

```python
@dataclass
class AssistantMessage:
    text: str | None   # plain text (or markdown if get_markdown=True)
    image: Path | None # path to downloaded image, or None
```

## API reference

Both `Gemini` and `ChatGPT` share the same interface — all methods below apply to both unless noted.

| Method | Description |
|---|---|
| `open_url(url, timeout)` | Open the chat interface in the browser |
| `send_message(message, submit, attachments, paste, fake_typing, typing_delay)` | Type and optionally submit a message |
| `query(message, timeout, attachments, paste, get_markdown, remove_watermark)` | Send a message, wait for the response, and return it |
| `get_last_response(get_markdown, remove_watermark)` | Retrieve the most recent response |
| `wait_until_idle(timeout)` | Block until the chatbot finishes generating |
| `get_state()` | Return the current UI state (`State.IDLE`, `GENERATING`, `TYPING`, `UPLOADING`) |
| `simple_query(prompt, attachments, timeout)` | Class method — open, query, close in one call |
| `short_wait()` | Sleep ~7 seconds |
| `long_wait()` | Sleep ~5 minutes |
| `refresh_page()` | Reload the current page |
| `close()` | Close the browser |
| `setup()` | One-time login setup (class method) |

See the [full documentation](https://hermex.usama.ai) for detailed guides on Gemini and ChatGPT.

### Constructor options

```python
Gemini(
    chrome_version=None,      # auto-detected from installed Chrome
    download_dir=Path("."),   # where generated images are saved
    headless=False,
    typing_delay=0.025,       # seconds between keystrokes
    disable_web_security=True,
)
# ChatGPT accepts the same parameters
```

## Watermark removal

Gemini watermarks its generated images. Pass `remove_watermark=True` to strip it:

```python
response = gemini.query("Generate an image of a sunset.", remove_watermark=True)
```

## Notes

- Bot detection is mitigated through per-character typing delays, fake typing before paste, a persistent browser profile, and a spoofed user agent. Avoid running headless for sensitive sessions.
- Browser profile and session data are stored in the platform data directory (`~/Library/Application Support/hermex` on macOS).
- This library relies on browser automation and may break if the UI changes. Use responsibly and be aware of each platform's terms of service.
