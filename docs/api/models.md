# Models

---

## AssistantMessage

Returned by `query()` and `get_last_response()`. Every response contains at least one of `text` or `image` — never both `None`.

::: hermex.models.AssistantMessage

---

## State

Represents the current UI state of the chatbot. Returned by `get_state()` and used internally by `wait_until_idle()`.

::: hermex.models.State
