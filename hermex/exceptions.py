class LoginRequiredError(Exception):
    """Raised when a login-gated feature is used without an active session.

    Run ``Gemini.setup()`` to log in and save a persistent session.
    """


class HeadlessClipboardError(Exception):
    """Raised when get_markdown=True is used in headless mode.

    Chrome's clipboard-write API silently no-ops in headless mode because the
    document never reports itself as focused, so there is no way to read back
    a "Copy response" click's result. Use get_markdown=False in headless mode,
    or run with headless=False.
    """
