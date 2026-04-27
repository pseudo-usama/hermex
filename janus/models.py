from dataclasses import dataclass
from pathlib import Path


@dataclass
class Response:
    text: str | None = None
    image: Path | None = None
