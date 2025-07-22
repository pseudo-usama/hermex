import time
import random
import undetected_chromedriver as uc
from config import chrome_data_dir


# Create a browser instance using undetected_chromedriver
options = uc.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-notifications")
options.add_argument(f"--user-data-dir={chrome_data_dir}")  # Use persistent profile
options.add_argument("--enable-javascript")
options.add_argument("--enable-cookies")
options.add_argument("--no-sandbox")
options.add_argument("--disable-web-security")
options.add_argument("--allow-running-insecure-content")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-features=IsolateOrigins,site-per-process")

# User agent of a real browser
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
options.add_argument(f"--user-agent={user_agent}")

# Create the undetected ChromeDriver with version matching your browser (138)
driver = uc.Chrome(options=options, use_subprocess=True, version_main=138)

# Simulate human-like behavior
def human_like_delay():
    time.sleep(random.uniform(1, 2))

# Navigate to the website with human-like behavior
driver.get("https://chatgpt.com")
human_like_delay()

# Move the mouse randomly to simulate human behavior (optional)
# If you need this, install pyautogui with: pip install pyautogui

input("Press Enter to close the browser...")
driver.quit()
