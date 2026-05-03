# Scraper

`Scraper` is the abstract base class shared by `Gemini` and `ChatGPT`. All public methods documented here are available on both.

::: hermex.scraper_base.Scraper
    options:
      members:
        - __init__
        - open_url
        - send_message
        - query
        - get_last_response
        - get_state
        - wait_until_idle
        - simple_query
        - setup
        - close
        - sleep
        - short_wait
        - long_wait
        - refresh_page
        - get_current_url
