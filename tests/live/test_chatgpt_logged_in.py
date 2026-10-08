"""Live logged-in ChatGPT tests. These drive the real chatgpt.com UI.

Signed out, chatgpt.com serves a different frontend, and `ChatGPT` branches on which
composer is mounted. This file covers the logged-in branch only; the signed-out one
lives in `test_chatgpt_logged_out.py`.

Every test here needs a logged-in profile — run `ChatGPT.setup()` and sign in first, or
they all fail at `test_detects_logged_in_session`.

Tests share a single browser session and therefore a single conversation, so order
matters: `test_fresh_page_is_idle` inspects an untouched composer and must come before
anything that types into it, and `test_sends_while_writing_block_is_open` must stay last
because it can leave an editable writing block behind it.
"""

import time
from pathlib import Path

import cv2
import numpy as np
import pytest
from selenium.webdriver.common.by import By

from hermex import ChatGPT, State


def _wait_until_leaves(bot: ChatGPT, state: State, timeout: float = 120) -> State:
    """Poll until `get_state()` is no longer `state`; return what it settled on.

    `_wait_until_state` needs a known target, which is the thing a transition test is
    trying to find out. This reports the state it landed on instead of timing out on a
    guess, so a wrong expectation fails with the actual value in the message.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        current = bot.get_state()
        if current is not state:
            return current
        time.sleep(1)
    raise AssertionError(f"Still {state} after {timeout}s.")


def test_page_loads(chatgpt: ChatGPT) -> None:
    assert "chatgpt.com" in chatgpt.get_current_url()


def test_detects_logged_in_session(chatgpt: ChatGPT) -> None:
    assert chatgpt.is_logged_in is True, (
        "Expected a logged-in profile. Run ChatGPT.setup() and sign in before "
        "running the live suite."
    )


def test_fresh_page_is_idle(chatgpt: ChatGPT) -> None:
    # The logged-in composer mounts the send button only once it holds content, so
    # get_state() reads that button's absence as IDLE.
    assert chatgpt.get_state() is State.IDLE


def test_state_transitions(chatgpt: ChatGPT) -> None:
    chatgpt.send_message("Write a 200-word poem about the sea.", submit=False)
    assert chatgpt.get_state() is State.TYPING

    chatgpt.send_message("")

    # Raises TimeoutException (test failure) if the state never turns GENERATING.
    chatgpt._wait_until_state(State.GENERATING, timeout=60)
    chatgpt.wait_until_idle()
    assert chatgpt.get_state() is State.IDLE


def test_query_returns_text(chatgpt: ChatGPT) -> None:
    res = chatgpt.query("Reply with only the number: 2 + 3")
    assert res.text is not None
    assert "5" in res.text


def test_query_returns_markdown(chatgpt: ChatGPT) -> None:
    # get_markdown=True goes through the 'Copy response' button and the OS clipboard,
    # a different path from reading .text — worth covering because it breaks on its own.
    res = chatgpt.query(
        "Reply with only this, as a markdown bullet list: apples, pears",
        get_markdown=True,
    )
    assert res.text is not None
    assert "-" in res.text or "*" in res.text


def test_send_recovers_stolen_focus(chatgpt: ChatGPT) -> None:
    # ChatGPT's writing block is an editable element that sometimes takes focus when a
    # response finishes, and paste=True inserts through document.execCommand, which writes to
    # whatever holds focus. Steal it with a control that is already on the page — no DOM
    # is added — and the message must still land in the composer. Without _focus() this
    # fails by sending nothing at all rather than by raising.
    chatgpt.driver.execute_script(
        "document.querySelector('button[aria-label=\"Start dictation\"]').focus();"
    )
    res = chatgpt.query("Reply with only the number: 7", paste=True, fake_typing=False)
    assert res.text is not None
    assert "7" in res.text


def test_multi_turn_conversation(chatgpt: ChatGPT) -> None:
    chatgpt.query("Remember this word: BANANA. Reply with only: OK")
    res = chatgpt.query(
        "What word did I ask you to remember? Reply with only that word."
    )
    assert res.text is not None
    assert "BANANA" in res.text.upper()


def test_upload_rejects_missing_file(chatgpt: ChatGPT, tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        chatgpt.send_message("Summarize this.", attachments=[tmp_path / "nope.png"])


def test_upload_rejects_unsupported_extension(chatgpt: ChatGPT, tmp_path: Path) -> None:
    script = tmp_path / "script.py"
    script.write_text("print('hello')")
    with pytest.raises(ValueError):
        chatgpt.send_message("Summarize this.", attachments=[script])


def test_upload_attachment_is_read_by_model(chatgpt: ChatGPT, tmp_path: Path) -> None:
    # A blue swatch, so a correct answer proves the file actually arrived and was
    # readable — not merely that the upload raised no exception. Faint noise in the
    # non-blue channels stops PNG compressing it down to a few KB, which keeps the
    # upload slow enough for UPLOADING to be observable.
    rng = np.random.default_rng(0)
    pixels = np.zeros((2500, 2500, 3), dtype=np.uint8)
    pixels[:, :, 0] = 255  # OpenCV is BGR, so channel 0 is blue
    pixels[:, :, 1] = rng.integers(0, 30, (2500, 2500), dtype=np.uint8)
    pixels[:, :, 2] = rng.integers(0, 30, (2500, 2500), dtype=np.uint8)
    swatch = tmp_path / "swatch.png"
    cv2.imwrite(str(swatch), pixels)

    # Attach on its own rather than through query(): send_message() waits the upload out
    # internally, so UPLOADING is only observable in between. The wait fails the test on
    # timeout, which is the point — this is the branch that had silently stopped working
    # on Gemini, where the send button stays enabled during an upload and the
    # disabled-attribute check never fired.
    chatgpt._upload_files([swatch])
    chatgpt._wait_until_state(State.UPLOADING, timeout=30)

    settled = _wait_until_leaves(chatgpt, State.UPLOADING)
    assert settled is State.TYPING, (
        f"Expected TYPING once the upload finished, got {settled}. An attachment with "
        "no text typed should still count as composer content."
    )

    res = chatgpt.query(
        "What single color fills this image? Reply with only the color name."
    )
    assert res.text is not None
    assert "blue" in res.text.lower()


def test_image_generation(chatgpt: ChatGPT) -> None:
    res = chatgpt.query("Generate an image of a plain solid red color background")
    assert res.image is not None, "ChatGPT returned no image for an image prompt."
    assert res.image.exists()

    img = cv2.imread(str(res.image))
    assert img is not None, f"Downloaded file is not a readable image: {res.image}"
    assert img.shape[0] > 0 and img.shape[1] > 0


def test_sends_while_writing_block_is_open(chatgpt: ChatGPT) -> None:
    # Must stay last: the writing block it opens stays open, and anything after it would
    # be running against a composer this test has already changed the context of.
    #
    # The writing block is another div[contenteditable="true"] and it renders ahead of
    # the composer, so an unscoped selector resolved to it and the next message was typed
    # into the document instead of being sent. Counting editables is how the bug is
    # detected without depending on a writing-block-specific selector. Whether ChatGPT
    # opens a writing block for any given prompt is its own call, so this skips rather
    # than fails when none appears.
    chatgpt.query("Use a writing block to write a three-sentence note about the sea.")

    editables = chatgpt.driver.find_elements(
        By.CSS_SELECTOR, 'div[contenteditable="true"]'
    )
    if len(editables) < 2:
        pytest.skip("ChatGPT opened no writing block for the probe prompt.")

    # Before the fix this returned nothing at all rather than raising: the text landed
    # in the writing block and the submit keystroke followed it there.
    res = chatgpt.query("Reply with only the number: 11")
    assert res.text is not None
    assert "11" in res.text
