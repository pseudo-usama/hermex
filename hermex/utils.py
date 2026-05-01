import re
import shutil
import subprocess
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


def copy_image_to_clipboard(image_path: Path):
    if sys.platform == "darwin":
        ext = image_path.suffix.lower()
        kind = "JPEG picture" if ext in (".jpg", ".jpeg") else "«class PNGf»"
        subprocess.run(
            [
                "osascript",
                "-e",
                f'set the clipboard to (read (POSIX file "{image_path.resolve()}") as {kind})',
            ],
            check=True,
        )
    elif sys.platform == "win32":
        raise NotImplementedError("Image clipboard not implemented for Windows.")
    elif sys.platform.startswith("linux"):
        raise NotImplementedError("Image clipboard not implemented for Linux.")
    else:
        raise NotImplementedError(
            f"Image clipboard not implemented for OS: {sys.platform}"
        )


def clear_data(data_dir=_default_data_dir):
    """
    Delete all data stored by Janus (browser profiles, etc.).

    :param data_dir: Root data directory to remove. Defaults to the platform-appropriate
        Janus data directory. Pass a custom path if you initialised scrapers with one.
    """
    data_dir = Path(data_dir).expanduser()
    if data_dir.exists():
        shutil.rmtree(data_dir)


def list_and_sort_dir(path):
    def natural_key(s):
        return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]

    path = Path(path) if not isinstance(path, Path) else path
    items = [item.name for item in path.iterdir()]
    items.sort(key=natural_key)

    return [path / item for item in items]
