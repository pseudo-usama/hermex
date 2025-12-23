import pyperclip
from shutil import move as move_file
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement

from scraper import Scraper
from scraper.config import SHORT_WAIT


class GeminiScraper(Scraper):
    def open_url(self, url="https://gemini.google.com"):
        super().open_url(url)
        return self

    def type_message(self, message: str, submit=True):
        wait = WebDriverWait(self.driver, 20)
        input_box = wait.until(
            EC.element_to_be_clickable((By.TAG_NAME, 'rich-textarea'))
        )
        input_box.click()
        self.sleep(0.5)
        input_p = input_box.find_element(By.TAG_NAME, 'p')

        super().type_message(message, input_p, submit=submit)
        return self

    def get_last_response(self, get_markdown=False):
        def _get_img(element: WebElement):
            element.find_element(By.TAG_NAME, "download-generated-image-button").click()
            img = self._get_downloaded_file()
            dest = self.download_dir / img.name
            move_file(img, dest)
            return dest

        def _get_text(element: WebElement, get_markdown):
            elem = element.find_element(By.CSS_SELECTOR, ".markdown")
            if not elem:
                raise TimeoutException("No text content found in the last response.")

            innerText = elem.text.strip()
            if innerText == "":
                return None

            if not get_markdown:
                return innerText

            element.find_element(By.TAG_NAME, "copy-button").click()
            self.sleep(0.5)
            return pyperclip.paste()

        wait = WebDriverWait(self.driver, 20)
        responses = wait.until(
            EC.presence_of_all_elements_located((By.TAG_NAME, 'model-response'))
        )
        last_response = responses[-1]
        try:
            text_content = _get_text(last_response, get_markdown)
        except Exception as e:
            print(f"Error getting text content: {e}")
            text_content = None
        try:
            img = _get_img(last_response)
        except Exception as e:
            print(f"Error getting image: {e}")
            img = None

        return text_content, img

    def select_nano_banana(self, delay=SHORT_WAIT):
        """Select the Nano Banana model on the Gemini page"""
        try:
            self.driver.find_element(By.TAG_NAME, "toolbox-drawer").click()
            self.sleep(0.5)
            self.driver.find_element(By.XPATH, "//div[contains(text(), 'Create images')]/ancestor::toolbox-drawer-item").click()
            self.sleep(delay)
        except Exception as e:
            print(f"Error selecting Nano Banana: {e}")
        return self


if __name__ == "__main__":
    scraper = GeminiScraper()

    try:
        scraper.open_url("https://gemini.google.com/app/a8089b0f67eaf42b")

        scraper.sleep(10)
        # scraper.select_nano_banana()
        initial_prompt = "What is peft"
        # scraper.type_message(initial_prompt)
        # scraper.sleep(60)
        response = scraper.get_last_response(get_markdown=True)
        print(f"Response: {response}")

        input("Press Enter to close the browser...")
    finally:
        scraper.close()
