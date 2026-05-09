from pathlib import Path

from platformdirs import user_data_dir

data_dir = Path(user_data_dir("hermex", appauthor=False))
LONG_WAIT = 5 * 60
SHORT_WAIT = 7
MIN_CHROME_VERSION = 130
