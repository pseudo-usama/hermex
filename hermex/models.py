from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class State(str, Enum):
    IDLE = "idle"
    """Page is ready and no activity is in progress. Safe to send the next message."""

    GENERATING = "generating"
    """The model is actively streaming a response. The stop button is visible."""

    TYPING = "typing"
    """The user (or automation) has content in the input box that has not been submitted yet."""

    UPLOADING = "uploading"
    """A file upload is in progress. The send button is visible but disabled and focusable."""


@dataclass
class Response:
    text: str | None = None
    image: Path | None = None
