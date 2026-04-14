import time
import random
import pyperclip
from pathlib import Path
from tempfile import TemporaryDirectory
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webelement import WebElement

from scraper.adaptive_delay import wait as long_sleep
from scraper.config import LONG_WAIT, SHORT_WAIT, chrome_data_dir, generated_imgs_dir


class Scraper:
    def __init__(self,
                 chrome_version=147,
                 download_dir=generated_imgs_dir,
                 headless=False,
                 typing_delay=0.025):
        self.chrome_data_dir = chrome_data_dir
        self.chrome_version = chrome_version
        self._temp_dir = TemporaryDirectory()
        self._selenium_download_dir = Path(self._temp_dir.name)
        self.download_dir = download_dir
        self.headless = headless
        self.driver = None
        self.typing_delay = typing_delay

        self.download_dir.mkdir(parents=True, exist_ok=True)

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

        options.add_experimental_option("prefs", {
            "download.default_directory": str(self._selenium_download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False
        })

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
        return self

    def open_url(self, url=None):
        if not self.driver:
            self.initialize_driver()

        self.driver.get(url)

        return self

    def type_message(self, message: str, input_box: WebElement, submit=True):
        for char in message:
            # self._send_key(input_box, char)
            if char == '\n':            # Handle Newline: Shift+Enter
                input_box.send_keys(Keys.SHIFT, Keys.ENTER)
            elif ord(char) > 0xFFFF:    # Handle Emojis: Copy and Paste
                pyperclip.copy(char)
                input_box.send_keys(Keys.COMMAND, 'v')
            else:
                input_box.send_keys(char)
            self.sleep(self.typing_delay)

        self.sleep(2)

        if submit:
            input_box.send_keys("\n")

        return self
    
    def paste_message(self, message: str, input_box: WebElement, submit=True, fake_typing=True):
        if fake_typing:
            self.type_message("Some fake text... " * 20, submit=False)
            input_box.send_keys(Keys.COMMAND, 'a')
            input_box.send_keys(Keys.BACKSPACE)

        pyperclip.copy(message)
        input_box.send_keys(Keys.COMMAND, 'v')
        self.sleep(2)

        if submit:
            input_box.send_keys("\n")

        return self

    def sleep(self, t):
        if t > 40:
            long_sleep(t)
            return self

        minmax_factor = 0.2
        min_time = t - t * minmax_factor
        max_time = t + t * minmax_factor
        time.sleep(random.uniform(min_time, max_time))

        return self

    def refresh_page(self):
        self.driver.refresh()
        return self

    def get_current_url(self, only_base=False):
        url = self.driver.current_url
        if only_base:
            return url.split("?")[0]
        return url
    
    def _get_downloaded_file(self, wait_time=60):
        """Wait for a file to be downloaded and return its path"""
        elapsed = 0
        poll_interval = 1
        while elapsed < wait_time:
            files = list(self._selenium_download_dir.iterdir())
            if files:
                return files[0]
            time.sleep(poll_interval)
            elapsed += poll_interval
        raise TimeoutException("File download timed out.")

    def close(self):
        """Close the browser and clean up"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def save_html_redirect(self, dir_path):
        url = self.get_current_url(only_base=True)
        dir_path.mkdir(parents=True, exist_ok=True)

        with open(dir_path / "open_chat.html", "w") as f:
            f.write(f'<!DOCTYPE html><meta http-equiv="refresh" content="0;url={url}">')

        return self
    
    @classmethod
    def simple_text_query(cls, prompt, wait=LONG_WAIT):
        """
        Send a text prompt to the chat interface.

        :param prompt: The prompt text to send.
        :param wait: Time to wait for the response in seconds.

        :return: The text response from the chat interface.
        """
        scraper = cls().initialize_driver()
        scraper.open_url().sleep(SHORT_WAIT)
        scraper.type_message(prompt).sleep(wait)

        text, _ = scraper.get_last_response()
        scraper.close()

        return text

    def n_prompts(self,
                  prompts,
                  delay=LONG_WAIT,
                  final_delay=SHORT_WAIT,
                  refresh=False):
        """
        Send multiple prompts to the chat interface.

        :param prompts: List of prompts to send.
        :param delay: Delay between each prompt in seconds.
        :param final_delay: Delay after the last prompt in seconds.
        :param refresh: Whether to refresh the page after each prompt.

        :return: List of responses, each containing text and image (if available).
        """
        responses = []

        for i, prompt in enumerate(prompts):
            print(f"Sending prompt {i + 1}/{len(prompts)}")
            self.type_message(prompt).sleep(delay)

            text, img = self.get_last_response()
            responses.append({ "text": text,"img": img })
            print(f"Response {i+1}: ",
                  "img," if img else "no image,",
                  "text" if text else "no text")

            if refresh:
                self.refresh_page()

            if i < len(prompts) - 1:
                self.sleep(delay)
            else:
                self.sleep(final_delay)

        return responses
