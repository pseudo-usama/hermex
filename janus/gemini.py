import pyperclip
from pathlib import Path
from shutil import move as move_file
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement

from janus import Scraper
from janus.gemini_watermark_remover import gemini_remove_watermark
from janus.utils import copy_image_to_clipboard
from janus.config import SUPPORTED_IMAGE_EXTENSIONS, SHORT_WAIT


class GeminiScraper(Scraper):
    def open_url(self, url="https://gemini.google.com"):
        super().open_url(url)
        return self

    def send_message(self,
                     message: str,
                     submit=True,
                     images: list[str | Path] = None,
                     paste=False,
                     fake_typing=True,
                     typing_delay: float = None):
        wait = WebDriverWait(self.driver, 20)
        input_box = wait.until(
            EC.element_to_be_clickable((By.TAG_NAME, 'rich-textarea'))
        )

        if images:
            self._upload_imgs(images, input_box)
            self.wait_until_send_button_enabled()

        input_box.click()
        self.sleep(0.5)
        input_p = input_box.find_element(By.TAG_NAME, 'p')

        if paste:
            self._paste_into(message, input_p, submit=submit, fake_typing=fake_typing, typing_delay=typing_delay)
        else:
            self._type_into(message, input_p, submit=submit, typing_delay=typing_delay)

        return self

    def get_last_response(self, get_markdown=False, remove_watermark=False):
        def _get_img(element: WebElement):
            element.find_element(By.TAG_NAME, "download-generated-image-button")\
                .find_element(By.TAG_NAME, "button").click()
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

        if remove_watermark and img is not None:
            gemini_remove_watermark(str(img), str(img))

        return text_content, img

    def _upload_imgs(self, image_paths: list[str | Path], input_box: WebElement):
        # TODO: This upload method would not work in headless mode
        resolved = []
        for image_path in image_paths:
            image_path = Path(image_path).resolve()
            if image_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
                raise ValueError(f"Unsupported file type '{image_path.suffix}'. Must be one of: {SUPPORTED_IMAGE_EXTENSIONS}")
            resolved.append(image_path)

        for image_path in resolved:
            copy_image_to_clipboard(image_path)
            self.sleep(0.3)

            input_box.click()
            self.sleep(0.5)
            self._paste()
            self.sleep(0.5)

    def wait_until_send_button_enabled(self, max_wait=60):
        for _ in range(max_wait):
            wait = WebDriverWait(self.driver, 20)
            send_button = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'button[aria-label="Send message"]'))
            )
            aria_disabled = send_button.get_attribute("aria-disabled")
            if aria_disabled == "false":
                break
            self.sleep(1)

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
        response = scraper.open_url("https://gemini.google.com") \
            .sleep(2) \
            .send_message("What is peft", paste=True) \
            .sleep(60) \
            .get_last_response(get_markdown=True)

        print(f"Response: {response}")
        input("Press Enter to close the browser...")
    finally:
        scraper.close()
