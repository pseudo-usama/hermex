from importlib.metadata import PackageNotFoundError, version

from hermex.chatgpt import ChatGPT
from hermex.exceptions import HeadlessClipboardError, LoginRequiredError
from hermex.gemini import Gemini
from hermex.gemini_watermark_remover import remove_gemini_watermark
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
    "HeadlessClipboardError",
    "Gemini",
    "ChatGPT",
    "remove_gemini_watermark",
    "clear_data",
    "__version__",
]
