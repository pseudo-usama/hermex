# Quickstart

## 1. Run setup

Before using Hermex for the first time, run setup for the scraper you plan to use. This builds a browser profile that looks like a real user, which significantly reduces bot detection risk.

```python
from hermex import Gemini, ChatGPT

Gemini.setup()   # for Gemini
ChatGPT.setup()  # for ChatGPT
```

A browser window will open. Browse around for a moment, then close the window. If you need features that require login (e.g. file upload on Gemini), log in during this session — Hermex will reuse the saved session in all future runs.

You only need to do this once. Repeat it if your session expires.

!!! note
    ChatGPT works without login for file upload and text queries, but image generation requires a logged-in session. For Gemini, guest mode supports basic text queries — file upload requires a logged-in session.

## 2. Send your first query

The simplest way is `simple_query()` — it opens the browser, sends your prompt, and closes the browser in one call:

```python
from hermex import Gemini

response = Gemini.simple_query("What is the capital of France?")
print(response.text)
```

## 3. Persistent session

For multiple queries in one script, instantiate the scraper directly instead of using `simple_query()`:

```python
from hermex import Gemini

gemini = Gemini()
gemini.open_url()

response = gemini.query("Summarize the history of the internet.")
print(response.text)

response = gemini.query("Now give me just the key dates.")
print(response.text)

gemini.close()
```

## 4. Attach a file

```python
from hermex import ChatGPT

chatgpt = ChatGPT()
chatgpt.open_url()

response = chatgpt.query("What's in this image?", attachments=["photo.jpg"])
print(response.text)

chatgpt.close()
```

## 5. Get a generated image

When the response includes a generated image, Hermex downloads it automatically:

```python
response = gemini.query("Generate an image of a mountain at sunset.")
print(response.image)  # Path to the downloaded file
```

## Next steps

- [Gemini guide](guides/gemini.md) — Gemini-specific features including watermark removal
- [ChatGPT guide](guides/chatgpt.md) — ChatGPT-specific tips and features
- [API reference](api/shared-interface.md) — full method reference
