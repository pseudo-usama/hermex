from importlib.metadata import PackageNotFoundError, version

from hermex.chatgpt import ChatGPT
from hermex.exceptions import LoginRequiredError
from hermex.gemini import Gemini
from hermex.models import AssistantMessage, State
from hermex.utils import clear_data

try:
    __version__ = version("hermex")
except PackageNotFoundError:  # running from a source tree without an install
    __version__ = "0.0.0+unknown"

__all__ = [
    "AssistantMessage",
    "State",
    "LoginRequiredError",
    "Gemini",
    "ChatGPT",
    "clear_data",
    "__version__",
]
