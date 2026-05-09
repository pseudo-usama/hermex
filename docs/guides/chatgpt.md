# ChatGPT Guide

## First-time setup

Run setup once before using ChatGPT. This builds a persistent browser profile that reduces bot detection risk:

```python
from hermex import ChatGPT

ChatGPT.setup()
```

Browse around briefly, then close the window. Login is optional — ChatGPT works without it for all features including image upload.

## Basic text query

```python
from hermex import ChatGPT

chatgpt = ChatGPT()
chatgpt.open_url()

response = chatgpt.query("Summarize the plot of Dune in three sentences.")
print(response.text)

chatgpt.close()
```

## Attaching files

ChatGPT supports file upload without requiring a logged-in session. Supported formats: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.pdf`, `.csv`, `.txt`, `.json`. You can also check `ChatGPT.SUPPORTED_ATTACHMENTS` at runtime.

```python
response = chatgpt.query(
    "Extract all the text from this image.",
    attachments=["receipt.jpg"],
)
print(response.text)
```

Multiple files:

```python
response = chatgpt.query(
    "What are the differences between these two screenshots?",
    attachments=["before.png", "after.png"],
)
```

## Getting generated images

When ChatGPT generates an image, Hermex downloads it automatically:

```python
response = chatgpt.query("Generate a logo for a coffee shop called 'Morning Brew'.")
if response.image:
    print(f"Image saved to: {response.image}")
```

ChatGPT does not watermark generated images.

## Getting markdown

Pass `get_markdown=True` to get the raw markdown source instead of plain text:

```python
response = chatgpt.query(
    "Give me a markdown cheatsheet.",
    get_markdown=True,
)
print(response.text)
```

## Long messages

Use `paste=True` for long prompts to avoid slow character-by-character typing:

```python
response = chatgpt.query(long_prompt, paste=True)
```

Hermex types dummy text first by default (`fake_typing=True`) before pasting to look more human. Disable if needed:

```python
response = chatgpt.query(long_prompt, paste=True, fake_typing=False)
```

## Multi-turn conversation

Each `query()` call appends to the existing conversation thread:

```python
chatgpt.open_url()

chatgpt.query("Act as a senior Python developer reviewing my code.")
response = chatgpt.query("Here's my function: ...")
print(response.text)

response = chatgpt.query("How would you refactor it?")
print(response.text)
```

## One-shot scripts

```python
from hermex import ChatGPT

response = ChatGPT.simple_query(
    "What does this error mean?",
    attachments=["traceback.png"],
)
print(response.text)
```

## Constructor options

```python
chatgpt = ChatGPT(
    download_dir="outputs/",   # where to save generated images
    headless=False,            # set True to run without a visible window
    typing_delay=0.025,        # seconds between keystrokes (default 0.025)
    data_dir=None,             # override the default data directory
)
```

!!! warning
    Avoid `headless=True` for sessions where bot detection is a concern. A visible browser is significantly harder to detect.
