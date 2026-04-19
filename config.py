from pathlib import Path


SUPPORTED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg'}
chrome_data_dir = Path("~/scraper_chrome_profile").expanduser()
generated_imgs_dir = Path("./generated_imgs")
LONG_WAIT = 5*60
SHORT_WAIT = 7
