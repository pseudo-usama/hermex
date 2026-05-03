# Gemini Guide

## First-time setup

Run setup once before using Gemini. This opens a browser so you can build a real user profile and optionally log in:

```python
from hermex import Gemini

Gemini.setup()
```

Browse around briefly, log in to your Google account if you want image upload support, then close the window.

## Guest mode vs logged-in mode

Gemini supports two modes:

| Feature | Guest mode | Logged in |
|---|---|---|
| Text queries | ✓ | ✓ |
| Image upload | ✗ | ✓ |
| Generated image download | ✓ | ✓ |

If you try to upload an image without being logged in, Hermex raises a `LoginRequiredError`.

## Basic text query

```python
from hermex import Gemini

gemini = Gemini()
gemini.open_url()

response = gemini.query("Explain how transformers work in simple terms.")
print(response.text)

gemini.close()
```

## Uploading images

Image upload requires a logged-in session. Supported formats: `.jpg`, `.jpeg`, `.png`.

```python
response = gemini.query(
    "What's wrong with this code?",
    images=["screenshot.png"],
)
print(response.text)
```

You can attach multiple images:

```python
response = gemini.query(
    "Compare these two diagrams.",
    images=["diagram1.png", "diagram2.png"],
)
```

## Getting generated images

When Gemini generates an image, Hermex downloads it automatically and returns the path:

```python
response = gemini.query("Generate an image of a futuristic city at night.")
if response.image:
    print(f"Image saved to: {response.image}")
```

By default images are saved to the current working directory. Change this with `download_dir`:

```python
gemini = Gemini(download_dir="outputs/")
```

## Watermark removal

Gemini watermarks its generated images. Pass `remove_watermark=True` to strip it automatically:

```python
response = gemini.query(
    "Generate an image of a sunset over the ocean.",
    remove_watermark=True,
)
```

This uses OpenCV template matching against the known watermark asset — no external service involved.

## Getting markdown

By default `query()` returns plain text. Pass `get_markdown=True` to get the raw markdown source instead:

```python
response = gemini.query(
    "Write a comparison table of Python web frameworks.",
    get_markdown=True,
)
print(response.text)  # raw markdown with table syntax
```

## Long messages

For long prompts, character-by-character typing is slow. Use `paste=True` to paste the message instead:

```python
response = gemini.query(long_prompt, paste=True)
```

By default, Hermex types some dummy text first before pasting (`fake_typing=True`) to avoid bot detection. You can disable this if needed:

```python
response = gemini.query(long_prompt, paste=True, fake_typing=False)
```

## Multi-turn conversation

`query()` always appends to the existing conversation. Just call it multiple times:

```python
gemini.open_url()

gemini.query("You are a helpful assistant. Let's work through a problem step by step.")
response = gemini.query("What is the time complexity of quicksort?")
print(response.text)

response = gemini.query("Now explain why the worst case happens.")
print(response.text)
```

## One-shot scripts

For scripts that just need a single answer, `simple_query()` handles everything:

```python
from hermex import Gemini

response = Gemini.simple_query("Translate 'hello world' to Spanish.")
print(response.text)
```

## Constructor options

```python
gemini = Gemini(
    download_dir="outputs/",   # where to save generated images
    headless=False,            # set True to run without a visible window
    typing_delay=0.025,        # seconds between keystrokes (default 0.025)
    data_dir=None,             # override the default data directory
)
```

!!! warning
    Avoid `headless=True` for sessions where bot detection is a concern. A visible browser is significantly harder to detect.
