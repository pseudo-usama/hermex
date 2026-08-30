---
description: API reference for Hermex exceptions — LoginRequiredError, HeadlessClipboardError, and how to handle missing login sessions or headless markdown limitations.
---

# Exceptions

---

## LoginRequiredError

Raised when a login-gated feature is attempted without an active session. Catch this to detect missing login and prompt the user to run `setup()`.

```python
from hermex import Gemini, LoginRequiredError

gemini = Gemini()
gemini.open_url()

try:
    response = gemini.query("Describe this image.", attachments=["photo.jpg"])
except LoginRequiredError:
    print("Please run Gemini.setup() and log in first.")
```

::: hermex.exceptions.LoginRequiredError

---

## HeadlessClipboardError

Raised when `get_markdown=True` is passed to `query()` or `get_last_response()` on an instance created with `headless=True`.

`get_markdown=True` works by clicking the platform's "Copy response" button and reading the result back from the OS clipboard. Chrome's clipboard-write API silently no-ops in headless mode because the document never reports itself as focused — there is no reliable workaround at the automation level, so Hermex raises immediately instead of returning stale or empty clipboard content.

```python
from hermex import ChatGPT, HeadlessClipboardError

chatgpt = ChatGPT(headless=True)
chatgpt.open_url()

try:
    response = chatgpt.query("Give me a markdown cheatsheet.", get_markdown=True)
except HeadlessClipboardError:
    print("Use get_markdown=False in headless mode, or run with headless=False.")
```

::: hermex.exceptions.HeadlessClipboardError
