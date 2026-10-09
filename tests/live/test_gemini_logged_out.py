"""Live signed-out Gemini tests. These drive gemini.google.com as a guest.

The fixture uses a throwaway profile without touching the saved Google login.
Guest coverage is limited to text queries and rejecting login-required uploads.
Tests share one conversation: inspect the fresh composer before sending messages.
Logged-in coverage lives in `test_gemini_logged_in.py`.
"""

from pathlib import Path

import pytest

from hermex import Gemini, LoginRequiredError, State


def test_page_loads(gemini_guest: Gemini) -> None:
    assert "gemini.google.com" in gemini_guest.get_current_url()


def test_detects_guest_session(gemini_guest: Gemini) -> None:
    assert gemini_guest.is_logged_in is False


def test_fresh_page_is_idle(gemini_guest: Gemini) -> None:
    assert gemini_guest.get_state() is State.IDLE


def test_upload_requires_login(gemini_guest: Gemini, tmp_path: Path) -> None:
    swatch = tmp_path / "swatch.png"
    swatch.write_bytes(b"\x89PNG\r\n\x1a\n")  # rejected before upload
    # Gemini guards login in send_message(), not in the private upload helper.
    with pytest.raises(LoginRequiredError):
        gemini_guest.send_message("Describe this image.", attachments=[swatch])


def test_state_transitions(gemini_guest: Gemini) -> None:
    gemini_guest.send_message("Write a 200-word poem about the sea.", submit=False)
    assert gemini_guest.get_state() is State.TYPING

    gemini_guest.send_message("")
    gemini_guest._wait_until_state(State.GENERATING, timeout=60)
    gemini_guest.wait_until_idle()
    assert gemini_guest.get_state() is State.IDLE


def test_query_returns_text(gemini_guest: Gemini) -> None:
    res = gemini_guest.query("Reply with only the number: 2 + 3")
    assert res.text is not None
    assert "5" in res.text


def test_multi_turn_conversation(gemini_guest: Gemini) -> None:
    gemini_guest.query("Remember this word: BANANA. Reply with only: OK")
    res = gemini_guest.query(
        "What word did I ask you to remember? Reply with only that word."
    )
    assert res.text is not None
    assert "BANANA" in res.text.upper()
