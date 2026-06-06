# Contributing to Hermex

Thanks for your interest in improving Hermex. Contributions are welcome — please read this file end-to-end before opening an issue or PR.

## Development setup

```bash
git clone https://github.com/pseudo-usama/hermex
cd hermex
pip install -e .
```

Requires Python 3.11+ and Google Chrome 130+.

Before pushing, format and lint:

```bash
make fmt
```

There is no test suite — Hermex drives real browsers against live web UIs, so behavior is verified by running the scrapers manually.

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
- If you change a public method's signature, update `README.md` and the relevant page under `docs/content/`
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
