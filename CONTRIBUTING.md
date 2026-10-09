# Contributing to Hermex

Thanks for your interest in improving Hermex. Contributions are welcome — please read this file end-to-end before opening an issue or PR.

## Development setup

```bash
git clone https://github.com/pseudo-usama/hermex
cd hermex
pip install -e ".[dev]"
```

Requires Python 3.11+ and Google Chrome 130+.

Before pushing, format and lint:

```bash
make fmt
```

Run the test suite for the platform you changed:

```bash
make test-gemini
make test-chatgpt
make test-live    # both
```

The tests live in `tests/live/` and drive the real ChatGPT and Gemini sites in a visible browser, with one logged-in and one logged-out file per platform. They are slow, use quota, and need a logged-in profile from `setup()`, so they run manually rather than in CI. Use the make targets rather than `pytest tests/live/`: the two logged-in suites share one Chrome profile and can't run in the same pytest invocation.

## Reporting bugs

To make a bug report useful, please include:

- **What you ran** — a minimal Python snippet that reproduces the issue
- **Browser + OS** — Chrome version and your operating system
- **The traceback** — full Python error, not just the last line
- **The relevant HTML snippet** *(optional, but very helpful)* — for selector-related bugs, open DevTools, inspect the element Hermex is failing on, and paste the surrounding HTML in the issue

## Pull requests

- Keep PRs small and focused on one change. A selector fix and a new feature should be separate PRs
- Update `CHANGELOG.md` with an entry under the `Unreleased` heading (follow the existing style — terse, technical, names the symptom and the actual fix).
- Match the existing code style — `make fmt` handles formatting, but also match naming and structure conventions of nearby code
- If you change a public method's signature, update `README.md` and the relevant page under `docs/content/docs/`
- Don't introduce new dependencies without a strong reason — Hermex aims to stay light

## Scope

**In scope:**
- Selector fixes when ChatGPT or Gemini update their UI
- New features that fit the existing fluent scraping interface
- Documentation improvements

**Out of scope:**
- Making Hermex "production-grade" — it deliberately drives a real browser and accepts the brittleness that comes with that
- Adding paid-API fallbacks — Hermex's whole point is no API keys
- Headless-by-default — sensitive sessions should run with a visible browser

## Questions

For anything you're unsure about, open a GitHub issue with the `question` label before starting work. Saves a round trip on the PR.
