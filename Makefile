.PHONY: fmt docs docs-build deploy

# macOS only: point Cairo (social-cards plugin) at Homebrew's lib dir. Must be set inline
# in each recipe — SIP strips DYLD_* from /bin/sh, so make-level `export` doesn't survive.
# Harmless no-op on Linux.
CAIRO_LIB := /opt/homebrew/lib

fmt:
	ruff format .
	ruff check --select I --fix .
	ruff check .

docs:
	cd docs && DYLD_FALLBACK_LIBRARY_PATH=$(CAIRO_LIB) mkdocs serve -a localhost:8080 --livereload

docs-build:
	cd docs && DYLD_FALLBACK_LIBRARY_PATH=$(CAIRO_LIB) mkdocs build

deploy: docs-build
	cd docs && firebase deploy
