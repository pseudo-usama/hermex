.PHONY: fmt typecheck test-gemini test-chatgpt test-live docs docs-build deploy

# macOS only: point Cairo (social-cards plugin) at Homebrew's lib dir. Must be set inline
# in each recipe — SIP strips DYLD_* from /bin/sh, so make-level `export` doesn't survive.
# Harmless no-op on Linux.
CAIRO_LIB := /opt/homebrew/lib

fmt:
	ruff format .
	ruff check --select I --fix .
	ruff check .

typecheck:
	mypy hermex/

# Drive the real UIs in a visible browser. Slow, use quota, and can fail for reasons
# outside the code (rate limits, captcha).
test-gemini:
	pytest tests/live/test_gemini.py -v

# Two files because chatgpt.com serves a different frontend signed out. They share one
# invocation safely: the guest fixture runs on a throwaway profile, not the real one.
test-chatgpt:
	pytest tests/live/test_chatgpt_logged_in.py tests/live/test_chatgpt_logged_out.py -v

# Two separate pytest runs, not `pytest tests/live/`: both suites hold a session-scoped
# browser on the same Chrome profile dir, so they cannot be alive at the same time.
test-live: test-gemini test-chatgpt

docs:
	cd docs && DYLD_FALLBACK_LIBRARY_PATH=$(CAIRO_LIB) mkdocs serve -a localhost:8080 --livereload

docs-build:
	cd docs && DYLD_FALLBACK_LIBRARY_PATH=$(CAIRO_LIB) mkdocs build

deploy: docs-build
	cd docs && firebase deploy
