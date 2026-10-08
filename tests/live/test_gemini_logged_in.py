"""Live logged-in Gemini tests. These drive the real gemini.google.com UI.

Run with a logged-in profile (see `Gemini.setup()`). Guest tests live separately
in `test_gemini_logged_out.py` and use a throwaway browser profile.

Tests share a single browser session and therefore a single conversation, so
order matters: anything that inspects a fresh/idle composer must come first, and
`test_followup_widget_text_is_stripped` must stay last because it starts a new
conversation.
"""

from pathlib import Path

import cv2
import numpy as np
import pytest

from hermex import Gemini, State


def test_page_loads(gemini: Gemini) -> None:
    assert "gemini.google.com" in gemini.get_current_url()


def test_detects_logged_in_session(gemini: Gemini) -> None:
    assert gemini.is_logged_in is True, (
        "Expected a logged-in profile. Run Gemini.setup() and sign in before "
        "running the live suite."
    )


def test_fresh_page_is_idle(gemini: Gemini) -> None:
    assert gemini.get_state() is State.IDLE


def test_state_transitions(gemini: Gemini) -> None:
    gemini.send_message("Write a 200-word poem about the sea.", submit=False)
    assert gemini.get_state() is State.TYPING

    gemini.send_message("")

    # Raises TimeoutException (test failure) if the state never turns GENERATING.
    gemini._wait_until_state(State.GENERATING, timeout=60)
    gemini.wait_until_idle()
    assert gemini.get_state() is State.IDLE


def test_query_returns_text(gemini: Gemini) -> None:
    res = gemini.query("Reply with only the number: 2 + 3")
    assert res.text is not None
    assert "5" in res.text


def test_multi_turn_conversation(gemini: Gemini) -> None:
    gemini.query("Remember this word: BANANA. Reply with only: OK")
    res = gemini.query(
        "What word did I ask you to remember? Reply with only that word."
    )
    assert res.text is not None
    assert "BANANA" in res.text.upper()


def test_upload_rejects_missing_file(gemini: Gemini, tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        gemini.send_message("Summarize this.", attachments=[tmp_path / "nope.png"])


def test_upload_rejects_unsupported_extension(gemini: Gemini, tmp_path: Path) -> None:
    script = tmp_path / "script.py"
    script.write_text("print('hello')")
    with pytest.raises(ValueError):
        gemini.send_message("Summarize this.", attachments=[script])


def test_upload_attachment_is_read_by_model(gemini: Gemini, tmp_path: Path) -> None:
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

    # Attach on its own rather than through query(): send_message() waits the upload
    # out internally, so UPLOADING is only observable in between. Both waits fail the
    # test on timeout. A finished upload reads as TYPING, not IDLE — the attached file
    # counts as composer input on its own, with no text typed.
    gemini._upload_files([swatch])
    gemini._wait_until_state(State.UPLOADING, timeout=30)
    gemini._wait_until_state(State.TYPING, timeout=120)

    res = gemini.query(
        "What single color fills this image? Reply with only the color name."
    )
    assert res.text is not None
    assert "blue" in res.text.lower()


def test_image_generation(gemini: Gemini) -> None:
    res = gemini.query("Generate an image of a plain solid red color background")
    assert res.image is not None, "Gemini returned no image for an image prompt."
    assert res.image.exists()

    img = cv2.imread(str(res.image))
    assert img is not None, f"Downloaded file is not a readable image: {res.image}"
    assert img.shape[0] > 0 and img.shape[1] > 0


# Gemini attaches its follow-up widget unpredictably — no prompt reliably forces it,
# which is why the test skips rather than fails when none shows up. These two are
# open-ended on the theory that it helps, which is a guess, not a measured result.
FOLLOW_UP_PROMPTS = (
    "Give me a one-paragraph overview of why the Roman Empire declined.",
    "Explain in one paragraph how the Silk Road shaped medieval trade.",
)


def test_followup_widget_text_is_stripped(gemini: Gemini) -> None:
    # Must run last: the fresh conversation below leaves the shared session on a new
    # thread, which would pull the rug out from under any test after it. The reset is
    # an attempt at better widget odds; it has not been shown to make a difference.
    gemini.open_url()

    for prompt in FOLLOW_UP_PROMPTS:
        res = gemini.query(prompt)
        suggestions = gemini._get_follow_up_suggestions()
        if suggestions:
            break
    else:
        pytest.skip("Gemini attached no follow-up widget to any probe prompt.")

    assert res.text is not None
    for suggestion in suggestions:
        assert suggestion not in res.text
        # The question line is the part that actually leaked before the fix.
        assert suggestion.splitlines()[0] not in res.text
