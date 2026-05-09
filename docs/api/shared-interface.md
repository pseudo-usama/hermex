# Shared Interface

`Gemini` and `ChatGPT` share the same interface — everything documented here applies to both. For platform-specific behavior, see the [Gemini](gemini.md) and [ChatGPT](chatgpt.md) pages.

---

## Constructor

Both scrapers accept the same constructor arguments. Pass these when instantiating `Gemini()` or `ChatGPT()`.

::: hermex.scraper_base.Scraper.__init__

---

## First-time setup

Run `setup()` once per machine before using Hermex for the first time. It builds a persistent browser profile that significantly reduces bot detection risk. If you need login-gated features (e.g. file upload on Gemini), log in during this session.

::: hermex.scraper_base.Scraper.setup

---

## Opening and closing the browser

::: hermex.scraper_base.Scraper.open_url

::: hermex.scraper_base.Scraper.close

---

## Sending queries

`query()` is the primary method for most use cases — it handles sending, waiting, and returning the response in one call. Use `send_message()` + `wait_until_idle()` + `get_last_response()` separately only when you need finer control.

::: hermex.scraper_base.Scraper.query

::: hermex.scraper_base.Scraper.simple_query

::: hermex.scraper_base.Scraper.send_message

---

## Waiting and responses

::: hermex.scraper_base.Scraper.wait_until_idle

::: hermex.scraper_base.Scraper.get_last_response

---

## State inspection

`get_state()` returns the current UI state of the chatbot. Useful for debugging or building custom polling logic. For most use cases, `wait_until_idle()` is sufficient.

::: hermex.scraper_base.Scraper.get_state

---

## Utilities

::: hermex.scraper_base.Scraper.sleep

::: hermex.scraper_base.Scraper.short_wait

::: hermex.scraper_base.Scraper.long_wait

::: hermex.scraper_base.Scraper.refresh_page

::: hermex.scraper_base.Scraper.get_current_url
