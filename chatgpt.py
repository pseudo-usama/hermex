import os
import time
import random
from pathlib import Path
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from config import chatgpt_download_imgs_dir


class ChatGPTScraper:
    def __init__(self, chrome_version=138, headless=False):
        self.chrome_data_dir = Path(os.path.join(os.getcwd(), "chrome-data")).absolute()
        self.chrome_version = chrome_version
        self.download_dir = chatgpt_download_imgs_dir
        self.headless = headless
        self.driver = None

    def initialize_driver(self):
        """Initialize and configure the Chrome driver"""
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument(f"--user-data-dir={self.chrome_data_dir}")  # Use persistent profile
        options.add_argument("--enable-javascript")
        options.add_argument("--enable-cookies")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-features=IsolateOrigins,site-per-process")

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        options.add_argument(f"--user-agent={user_agent}")

        if self.download_dir:
            prefs = {
                "download.default_directory": os.path.abspath(self.download_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False
            }
            options.add_experimental_option("prefs", prefs)

        if self.headless:
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")

        # Create the undetected ChromeDriver with version matching your browser
        self.driver = uc.Chrome(
            options=options, 
            use_subprocess=True, 
            version_main=self.chrome_version
        )
        return self.driver

    def open_url(self, url="https://chatgpt.com"):
        if not self.driver:
            self.initialize_driver()

        self.driver.get(url)

        return self.driver

    def type_message(self, message, submit=True):
        try:
            # Wait for the input field to be available (adjust selector as needed)
            wait = WebDriverWait(self.driver, 20)
            input_box = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[contenteditable="true"]'))
            )

            # Click the input field
            input_box.click()
            self.human_like_delay(0.5, 0.6)

            for char in message:
                if char == '\n':
                    # For newlines, press Shift+Enter instead of just Enter
                    input_box.send_keys('\ue008' + '\n')    # \ue008 is Shift key
                    input_box.send_keys('\ue008')           # Release the Shift key
                else:
                    input_box.send_keys(char)
                time.sleep(random.uniform(0.01, 0.05))

            self.human_like_delay()

            if submit:
                input_box.send_keys("\n")

            return True

        except TimeoutException:
            print("Could not find the input field. The page might have changed or is not loaded.")
            return False

    def download_last_generated_image(self):
        wait = WebDriverWait(self.driver, 15)
        responses = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".agent-turn"))
        )

        if not responses:
            raise TimeoutException("No responses found in the chat.")

        # Click the last response img to ensure images are loaded
        image_elements = responses[-1].find_elements(By.CSS_SELECTOR, "img")
        if not image_elements:
            raise TimeoutException("No images found in the last response.")
        image_elements[0].click()

        self.human_like_delay(15, 20)

        # Now click the download button
        down_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".flex.items-center.justify-self-end.text-end > span:nth-of-type(4)")))
        if not down_btn:
            raise TimeoutException("Download button not found.")
        down_btn.click()

    def get_last_response(self):
        pass

    def human_like_delay(self, min_time=1, max_time=2):
        time.sleep(random.uniform(min_time, max_time))

    def refresh_page(self):
        """Refresh the current page"""
        self.driver.refresh()

    def get_current_url(self, only_base=False):
        if only_base:
            return self.driver.current_url.split("?")[0]
        return self.driver.current_url

    def close(self):
        """Close the browser and clean up"""
        if self.driver:
            self.driver.quit()
            self.driver = None


if __name__ == "__main__":
    scraper = ChatGPTScraper()

    try:
        scraper.initialize_driver()
        scraper.open_url()

        initial_prompt = "Write a short poem about artificial intelligence"
        scraper.type_message(initial_prompt)
        
        input("Press Enter to close the browser...")
    finally:
        scraper.close()
