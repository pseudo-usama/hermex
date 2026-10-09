# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Hermex** is a Python library (published on PyPI as `hermex`) that drives the free web
UIs of ChatGPT and Google Gemini through a real Chrome browser, so scripts can send
prompts, attach files, and get back text responses and generated images without an API
key. It is built on Selenium with `undetected-chromedriver`.

The scrapers depend on the live page structure of both sites, so most maintenance is
keeping them working after a UI change. The code comments next to each lookup explain
why it is done that way — read them before changing one.

## Repository Layout

```
hermex/                 the package
  scraper_base.py       Scraper — abstract base: browser lifecycle, typing, waiting, downloads
  gemini.py             Gemini scraper
  chatgpt.py            ChatGPT scraper
  gemini_watermark_remover.py   OpenCV watermark removal for Gemini images
  models.py             AssistantMessage, State
  exceptions.py         LoginRequiredError, HeadlessClipboardError
  config.py, utils.py   data dir, timing constants, user agent, clear_data()
  assets/               reference images used by the watermark remover — do not modify
tests/live/             pytest suites that drive the real sites
docs/                   MkDocs documentation site
.github/workflows/      lint on PRs to main; publish to PyPI on a v* tag
```

## Components

- **Scrapers.** `Gemini` and `ChatGPT` subclass `Scraper` and share one public interface:
  `open_url()`, `query()`, `send_message()`, `wait_until_idle()`, `get_last_response()`,
  `get_state()`, `simple_query()`, and `setup()`. The base class owns everything
  platform-agnostic; subclasses implement the page-specific parts. Most methods return
  `self` so calls can be chained.
- **Sessions.** Each scraper runs on a persistent Chrome profile in the platform data
  directory, so a login made during `setup()` carries over to later runs. Don't clear it
  accidentally.
- **Guest mode.** Both scrapers handle text queries without a login. Login-only features
  are file upload and image generation on both. File upload raises `LoginRequiredError`
  when signed out. A signed-out image prompt raises nothing; the reply is just text. ChatGPT
  serves a separate frontend to signed-out visitors, so `chatgpt.py` handles two page
  layouts.
- **Bot evasion.** This uses typing with a delay per character, fake typing before
  pastes, a spoofed user agent, and the undetected driver. Keep all of it intact.
- **Watermark removal.** Gemini images can optionally have their watermark removed. The
  function is also exported on its own as `remove_gemini_watermark()`.

The public API is whatever `hermex/__init__.py` exports.

## Commands

```bash
pip install -e ".[dev]"   # package + ruff, mypy, pytest, mkdocs

make fmt                  # ruff format + import sort + lint
make typecheck            # mypy hermex/

make test-gemini          # live tests, visible browser
make test-chatgpt
make test-live            # both, as two separate pytest runs

make docs                 # serve docs at localhost:8080
make docs-build
make deploy               # build and deploy the docs site to Firebase Hosting
```

## Tests

The tests under `tests/live/` run against the real sites. They are slow, use quota, need a
logged-in profile from `setup()`, and can fail for reasons outside the code (rate limits,
captchas). That is why they run by hand and not in CI. Each platform has a logged-in file
and a logged-out file. The logged-out fixtures use throwaway profiles and leave the saved
login alone.

Run at most one logged-in suite per pytest invocation. Both logged-in suites use the same
Chrome profile, and two Chrome instances can't share a profile at once. This means
`pytest tests/live/` fails, so use the make targets. See `tests/live/conftest.py` and the
test files for the ordering constraints.

## Documentation Site

`docs/` is a MkDocs (Material theme) site, hosted at https://hermex.usama.ai. The guides
are written by hand. The API reference pages are generated from docstrings with
mkdocstrings, so docstrings are user-facing. The landing page is `docs/content/index.html`,
the docs live under `docs/content/docs/`, and the changelog page pulls in `CHANGELOG.md`.

## Conventions

- Add an entry under `## [Unreleased]` in `CHANGELOG.md` for every user-visible change.
- If you change public behavior or a signature, update `README.md` and the matching pages
  under `docs/content/docs/`.
- Keep dependencies minimal.
