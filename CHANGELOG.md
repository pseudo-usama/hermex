# Changelog

## [0.1.0] - 2026-05-03

### Added
- Initial release
- Gemini scraper with text queries, image upload, and watermark removal
- ChatGPT scraper with text queries and image upload
- Persistent Chrome profile with bot detection evasion
- First-time setup via `Gemini.setup()` / `ChatGPT.setup()`
- `query()` — send a message, wait for response, and return it in one call
- `send_message()` — type and optionally submit a message with simulated keystrokes
- `get_last_response()` — retrieve the most recent response as an `AssistantMessage`
- `get_state()` — inspect the current UI state (`IDLE`, `GENERATING`, `TYPING`, `UPLOADING`)
- `wait_for_page_load()` — block until the chat interface is ready to interact with
- `simple_query()` — open browser, send prompt, close browser in one call
- `sleep()` — human-like sleep with random jitter
- `short_wait()` — convenience sleep of ~7 seconds
- `long_wait()` — convenience sleep of ~5 minutes
- `refresh_page()` — reload the current page
- `get_current_url()` — return the current browser URL
