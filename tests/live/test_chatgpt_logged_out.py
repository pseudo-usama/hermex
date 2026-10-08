"""Live signed-out ChatGPT tests. These drive the real chatgpt.com UI as a guest.

Signed out, chatgpt.com serves a different frontend — its form posts to
`/unauth-mweb/conversation`, the composer is a plain `<textarea>` rather than a
contenteditable div, and one always-mounted submit button swaps the icon inside it
instead of there being a separate stop button. `ChatGPT` branches on which composer is
mounted; this file covers that branch, and `test_chatgpt_logged_in.py` covers the other.

OpenAI gates file upload and image generation behind a login here, so guest support is
text queries only — `test_upload_requires_login` pins that down rather than testing an
upload.

The fixture builds a throwaway Chrome profile, so these can run alongside a logged-in
suite. Tests share one conversation, so order matters: everything that inspects an
untouched composer comes before anything that types into it.
"""

from pathlib import Path

import pytest

from hermex import ChatGPT, LoginRequiredError, State


def test_page_loads(chatgpt_guest: ChatGPT) -> None:
    assert "chatgpt.com" in chatgpt_guest.get_current_url()


def test_detects_guest_session(chatgpt_guest: ChatGPT) -> None:
    # The guest composer is itself the signal, so this also confirms
    # wait_for_page_load() resolved the signed-out composer rather than timing out.
    assert chatgpt_guest.is_logged_in is False


def test_fresh_page_is_idle(chatgpt_guest: ChatGPT) -> None:
    # The guest submit button is always mounted and reports an empty composer through
    # aria-disabled, so its presence alone must not read as content.
    assert chatgpt_guest.get_state() is State.IDLE


def test_upload_requires_login(chatgpt_guest: ChatGPT, tmp_path: Path) -> None:
    swatch = tmp_path / "swatch.png"
    swatch.write_bytes(b"\x89PNG\r\n\x1a\n")  # never reaches the browser
    with pytest.raises(LoginRequiredError):
        chatgpt_guest._upload_files([swatch])


def test_state_transitions(chatgpt_guest: ChatGPT) -> None:
    chatgpt_guest.send_message("Write a 200-word poem about the sea.", submit=False)
    assert chatgpt_guest.get_state() is State.TYPING

    # Submits by clicking the composer's own button — Enter in a <textarea> would only
    # insert a newline.
    chatgpt_guest.send_message("")

    # Raises TimeoutException (test failure) if the state never turns GENERATING. The
    # guest build signals it through two hidden spans inside the submit button that
    # un-hide in turn, so this covers both.
    chatgpt_guest._wait_until_state(State.GENERATING, timeout=60)

    # Well short of the 300s default: a short poem that takes minutes means the state
    # machine is wrong, and failing fast beats waiting out the full timeout.
    chatgpt_guest.wait_until_idle(timeout=120)
    assert chatgpt_guest.get_state() is State.IDLE


def test_query_returns_text(chatgpt_guest: ChatGPT) -> None:
    res = chatgpt_guest.query("Reply with only the number: 2 + 3")
    assert res.text is not None
    assert "5" in res.text


def test_query_returns_markdown(chatgpt_guest: ChatGPT) -> None:
    # get_markdown=True goes through the 'Copy response' button and the OS clipboard, a
    # different path from reading .text. The signed-out build labels that button the
    # same way the authed one does, but unlike the rest of the guest selectors this one
    # is inferred from a page-wide button list, not from the response DOM itself.
    res = chatgpt_guest.query(
        "Reply with only this, as a markdown bullet list: apples, pears",
        get_markdown=True,
    )
    assert res.text is not None
    assert "-" in res.text or "*" in res.text
