import re
import sys
import subprocess
from pathlib import Path


def copy_image_to_clipboard(image_path: Path):
    if sys.platform == 'darwin':
        ext = image_path.suffix.lower()
        kind = 'JPEG picture' if ext in ('.jpg', '.jpeg') else '«class PNGf»'
        subprocess.run(
            ['osascript', '-e', f'set the clipboard to (read (POSIX file "{image_path.resolve()}") as {kind})'],
            check=True
        )
    elif sys.platform == 'win32':
        raise NotImplementedError("Image clipboard not implemented for Windows.")
    elif sys.platform.startswith('linux'):
        raise NotImplementedError("Image clipboard not implemented for Linux.")
    else:
        raise NotImplementedError(f"Image clipboard not implemented for OS: {sys.platform}")


def list_and_sort_dir(path):
    def natural_key(s):
        return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]

    path = Path(path) if not isinstance(path, Path) else path
    items = [item.name for item in path.iterdir()]
    items.sort(key=natural_key)

    return [path / item for item in items]
