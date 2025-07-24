import time
import random
from pathlib import Path
from shutil import move as move_file
from tempfile import TemporaryDirectory
import undetected_chromedriver as uc
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains

import scraper.adaptive_delay as ad
from scraper.config import chrome_data_dir, generated_imgs_dir


ad.start_console_listener()


class ChatGPTScraper:
    def __init__(self,
                 chrome_version=138,
                 download_dir=generated_imgs_dir,
                 headless=False):
        self.chrome_data_dir = chrome_data_dir
        self.chrome_version = chrome_version
        self._temp_dir = TemporaryDirectory()
        self._selenium_download_dir = Path(self._temp_dir.name)
        self.download_dir = download_dir
        self.headless = headless
        self.driver = None

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

    def open_url(self, url="https://chatgpt.com"):
        if not self.driver:
            self.initialize_driver()

        self.driver.get(url)

        return self

    def type_message(self, message, submit=True):
        # Wait for the input field to be available (adjust selector as needed)
        wait = WebDriverWait(self.driver, 20)
        input_box = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[contenteditable="true"]'))
        )

        # Click the input field
        input_box.click()
        self.sleep(0.5)

        for char in message:
            if char == '\n':
                # For newlines, press Shift+Enter instead of just Enter
                input_box.send_keys('\ue008' + '\n')    # \ue008 is Shift key
                input_box.send_keys('\ue008')           # Release the Shift key
            else:
                input_box.send_keys(char)
            self.sleep(0.025)

        self.sleep(2)

        if submit:
            input_box.send_keys("\n")

        return self

    def get_last_response(self):
        def _get_img(element: WebElement):
            image_elems = element.find_elements(By.CSS_SELECTOR, "img")
            if not image_elems:
                raise TimeoutException("No images found in the last response.")
            image_elems[0].click()

            self.sleep(20)

            down_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "header.grid > div:nth-of-type(2) button:nth-of-type(4)")))
            if not down_btn:
                raise TimeoutException("Download button not found.")
            down_btn.click()
            self.sleep(5)

            img = list(self._selenium_download_dir.iterdir())[0]
            dest = self.download_dir / img.name
            move_file(img, dest)

            # try:    # Press ESC key to close image dialog
            #     actions = ActionChains(self.driver)
            #     actions.send_keys('\ue00c')  # ESC key
            #     actions.perform()
            #     self.sleep(1)
            # except Exception as e:
            #     print(f"Error while pressing ESC key: {e}")

            return dest

        def _get_text(element: WebElement):
            elem = element.find_element(By.CSS_SELECTOR, ".markdown")
            if not elem:
                raise TimeoutException("No text content found in the last response.")

            return elem.text

        wait = WebDriverWait(self.driver, 15)
        responses = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".agent-turn"))
        )

        if not responses:
            raise TimeoutException("No responses found in the chat.")

        last_response = responses[-1]
        try:
            text_content = _get_text(last_response)
        except Exception as e:
            print(f"Error getting text content: {e}")
            text_content = None
        try:
            img = _get_img(last_response)
        except Exception as e:
            print(f"Error getting image: {e}")
            img = None

        return text_content, img

    def sleep(self, t):
        if t > 40:
            ad.wait(t)
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

    def _goto_model(self, model, delay=7):
        # url = self.get_current_url(only_base=True)
        # self.open_url(f"{url}?model={model}")

        self.driver.find_element(By.CSS_SELECTOR, f'header button[aria-label^="Model selector"]').click()
        self.sleep(0.5)
        self.driver.find_element(By.CSS_SELECTOR, f'div[data-testid="model-switcher-{model}"]').click()
        self.sleep(delay)

        return self

    def goto_gpt4o(self, delay=7):
        self._goto_model("gpt-4o", delay)
        return self

    def goto_o3(self, delay=7):
        self._goto_model("o3", delay)
        return self

    def close(self):
        """Close the browser and clean up"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def n_prompts(self, prompts, delay=5*60, final_delay=7, refresh=False):
        """
        Send multiple prompts to the chat interface.
        
        :param prompts: List of prompts to send.
        :param delay: Delay between each prompt in seconds.
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

    def save_html_redirect(self, dir_path):
        url = self.get_current_url(only_base=True)
        dir_path.mkdir(parents=True, exist_ok=True)

        with open(dir_path / "open_chat.html", "w") as f:
            f.write(f'<!DOCTYPE html><meta http-equiv="refresh" content="0;url={url}">')

        return self


if __name__ == "__main__":
    scraper = ChatGPTScraper()

    try:
        scraper.open_url()

        initial_prompt = "Write a short poem about artificial intelligence"
        scraper.type_message(initial_prompt)
        
        input("Press Enter to close the browser...")
    finally:
        scraper.close()
