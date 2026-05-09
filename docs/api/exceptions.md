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
