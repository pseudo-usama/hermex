class LoginRequiredError(Exception):
    """Raised when a login-gated feature is used without an active session.

    Run ``Gemini.setup()`` to log in and save a persistent session.
    """
