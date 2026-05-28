# Changelog

## [0.4.1] - 2026-05-28

### Fixed
- `Gemini.get_state()` rewritten for the latest UI: the send/stop button moved out of `[data-node-type="input-area"]` and the mic-button container is no longer the source of truth for whether the input has content. State is now derived from the `[data-test-id="send-button-container"]` element — `stop` class → `GENERATING`, missing `has-input` class → `IDLE`, `aria-disabled="true"` → `UPLOADING`, otherwise `TYPING`. Works on both desktop and mobile layouts
- `Gemini.get_last_response()` now waits ~1.5 s before clicking the image download button, giving the button time to become responsive after the response finishes rendering

### Added
- `simple_query()` now accepts `paste`, `fake_typing`, `typing_delay`, `get_markdown`, and `remove_watermark`, forwarding them to `query()`

### Changed
- `send_message()` argument order changed — `submit` moved to the end of the parameter list. Calls passing `submit` positionally must be updated; keyword calls are unaffected
- `query()` and `simple_query()` argument order changed — `timeout` moved to the end of the parameter list (the two now share an identical parameter order). Calls passing `timeout` positionally must be updated; keyword calls are unaffected
- Docstrings for shared arguments aligned across `send_message()`, `query()`, and `simple_query()` for consistency
- `ChatGPT.send_message()` and `Gemini.send_message()` signatures aligned with the base `Scraper.send_message()` (added type hints)
- Fluent `Scraper` methods (those returning `self`, e.g. `open_url()`, `send_message()`, `short_wait()`) are now annotated with `typing.Self`, so type checkers preserve the concrete subclass type through chained calls

## [0.3.0] - 2026-05-27

### Added
- `hermex.__version__` attribute, derived from the installed package metadata

### Changed
- `simple_query()` parameter `prompt` renamed to `message` for consistency with `send_message()` and `query()`, which already use `message`

### Fixed
- `Gemini` file upload updated for the latest UI: the upload-menu button's `aria-label` changed from `Open upload file menu` to `Upload & tools`, and the "Upload files" trigger is now located via the shared `images-files-uploader[data-test-id="uploader-images-files-button-advanced"]` wrapper so it resolves correctly in both the maximized and narrow/mobile menu layouts
- `Gemini` file upload now restores the patched `HTMLInputElement.prototype.click` even when an intermediate step fails (best-effort restore in `try/finally`), preventing the override from leaking into the page without masking the original error

## [0.2.1] - 2026-05-18

### Fixed
- Corrected documentation for ChatGPT login requirements — file upload works without login; only image generation requires a logged-in session
- `ChatGPT.get_state()` now correctly returns `GENERATING` during image generation — after a recent ChatGPT UI update, the stop button disappears while the image loading skeleton is still visible, causing the state to appear idle prematurely; fixed by additionally checking for `[data-testid="image-gen-loading-state"]`
- `ChatGPT.get_last_response()` no longer raises a spurious "neither text nor image" error on image-only responses — the `<img>` tag is now awaited for up to 5 seconds to account for the brief DOM delay after the loading skeleton clears

## [0.2.0] - 2026-05-09

### Added
- `SUPPORTED_ATTACHMENTS` class constant on `Gemini` and `ChatGPT` — exposes the set of allowed file extensions per platform

### Changed
- `images` parameter renamed to `attachments` in `send_message()`, `query()`, and `simple_query()` across both scrapers
- Supported upload types expanded from images only to include `.pdf`, `.csv`, `.txt`, `.json`, `.gif`, `.webp`

### Fixed
- `ChatGPT._detect_login()` now uses `WebDriverWait` with `TimeoutException` instead of a bare `find_element` with `except Exception`, consistent with Gemini's approach
- `_detect_chrome_version()` now raises a clear `RuntimeError` when Chrome is not found, the subprocess fails, or the version string cannot be parsed — previously crashed with a cryptic `TypeError` or `AttributeError`
- `close()` now calls `self._temp_dir.cleanup()` to release the temporary download directory
- `setup()` browser-close detection now catches `WebDriverException` instead of bare `Exception`, and wraps the loop in `try/finally` to guarantee `close()` is always called
- `_get_downloaded_file()` now filters out `.crdownload` partial files to avoid returning incomplete downloads
- `simple_query()` now wraps the query in `try/finally` so the browser is always closed even if an exception is raised
- File existence is now checked before upload in both scrapers — raises `FileNotFoundError` with a clear message instead of a cryptic driver error
- `TemporaryDirectory` creation moved from `__init__` to `_initialize_driver()` so its lifecycle matches the driver — reusing an instance after `close()` no longer points Chrome at a deleted download directory, and calling `close()` twice is now a safe no-op

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
