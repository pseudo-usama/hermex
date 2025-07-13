import re
from pathlib import Path


def list_and_sort_dir(path):
    def natural_key(s):
        return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]

    path = Path(path) if not isinstance(path, Path) else path
    items = [item.name for item in path.iterdir()]
    items.sort(key=natural_key)

    return [path / item for item in items]
