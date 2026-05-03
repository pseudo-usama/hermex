from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class State(str, Enum):
    """Current UI state of the chatbot interface."""

    IDLE = "idle"
    """Ready and waiting for input."""

    GENERATING = "generating"
    """Model is actively producing a response."""

    TYPING = "typing"
    """Input box has content that has not been submitted yet."""

    UPLOADING = "uploading"
    """A file upload is in progress."""


@dataclass
class Response:
    """Result returned by `query()` and `get_last_response()`."""

    text: str | None = None
    """Plain text content of the response, or markdown if `get_markdown=True`. None if the response is image-only."""

    image: Path | None = None
    """Path to the downloaded image file. None if the response contains no image."""
