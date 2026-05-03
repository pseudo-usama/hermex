from pathlib import Path

from platformdirs import user_data_dir

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
data_dir = Path(user_data_dir("hermex", appauthor=False))
LONG_WAIT = 5 * 60
SHORT_WAIT = 7
MIN_CHROME_VERSION = 130
