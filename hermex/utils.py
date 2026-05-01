import shutil
import sys
from pathlib import Path

from hermex.config import data_dir as _default_data_dir


def get_user_agent(chrome_version: int) -> str:
    version_str = f"{chrome_version}.0.0.0"
    if sys.platform == "darwin":
        return (
            f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            f"AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/{version_str} Safari/537.36"
        )
    elif sys.platform == "win32":
        return (
            f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            f"AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/{version_str} Safari/537.36"
        )
    elif sys.platform.startswith("linux"):
        return (
            f"Mozilla/5.0 (X11; Linux x86_64) "
            f"AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/{version_str} Safari/537.36"
        )
    else:
        raise NotImplementedError(
            f"User agent not defined for platform: {sys.platform}"
        )


def clear_data(data_dir=_default_data_dir):
    """
    Delete all data stored by Hermex (browser profiles, etc.).

    :param data_dir: Root data directory to remove. Defaults to the platform-appropriate
        Hermex data directory. Pass a custom path if you initialised scrapers with one.
    """
    data_dir = Path(data_dir).expanduser()
    if data_dir.exists():
        shutil.rmtree(data_dir)


