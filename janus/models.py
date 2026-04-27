from pathlib import Path
from dataclasses import dataclass


@dataclass
class Response:
    text: str | None = None
    image: Path | None = None
