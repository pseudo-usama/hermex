from pathlib import Path

import pyperclip
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from hermex.config import SHORT_WAIT, SUPPORTED_IMAGE_EXTENSIONS
from hermex.models import Response, State
from hermex.scraper_base import Scraper


class ChatGPT(Scraper):
    """
    Scraper for ChatGPT (chatgpt.com).

    Currently supports text queries only. Image upload is not yet implemented.
    Not part of the public API -- use Gemini instead until this class is complete.
    """

    def open_url(self, url="https://chatgpt.com", timeout=30):
        if "chatgpt.com" not in url:
            raise ValueError(f"Expected a chatgpt.com URL, got: {url}")
        super().open_url(url, timeout)
        return self

    def wait_for_page_load(self, timeout: float = 30) -> None:
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'div[contenteditable="true"]')
            )
        )

    def _detect_login(self):
        try:
            self.driver.find_element(
                By.CSS_SELECTOR, 'button[data-testid="login-button"]'
            )
            self.is_logged_in = False
        except Exception:
            self.is_logged_in = True

    def send_message(
        self,
        message,
        submit=True,
        images: list[str | Path] = None,
        paste=False,
        fake_typing=True,
        typing_delay: float = None,
    ):
        if images:
            self._upload_imgs(images)

        wait = WebDriverWait(self.driver, 20)
        input_box = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[contenteditable="true"]'))
        )
        input_box.click()
        self.sleep(0.5)

        if paste:
            self._paste_into(
                message, input_box, fake_typing=fake_typing, typing_delay=typing_delay
            )
        else:
            self._type_into(message, input_box, typing_delay=typing_delay)

        if submit:
            input_box.send_keys("\n")

        if images:
            self._wait_until_state(State.TYPING)

        return self

    def _upload_imgs(self, image_paths: list[str | Path]):
        resolved = []
        for image_path in image_paths:
            image_path = Path(image_path).resolve()
            if image_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
                raise ValueError(
                    f"Unsupported file type '{image_path.suffix}'. Must be one of: {SUPPORTED_IMAGE_EXTENSIONS}"
                )
            resolved.append(image_path)

        file_input = self.driver.find_element(By.CSS_SELECTOR, "#upload-photos")
        self.driver.execute_script("arguments[0].style.display = 'block';", file_input)
        file_input.send_keys("\n".join(str(p) for p in resolved))

    def get_last_response(self, get_markdown=False, remove_watermark=False) -> Response:
        # ChatGPT does not watermark generated images, so remove_watermark is a no-op.

        def _get_img(element: WebElement):
            image_elems = element.find_elements(By.CSS_SELECTOR, "img")
            if not image_elems:
                raise NoSuchElementException("No image element in this response.")
            self.driver.execute_script("arguments[0].click();", image_elems[0])
            self.sleep(2)
            down_btn = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'header button[aria-label="Save"]')
                )
            )
            self.driver.execute_script("arguments[0].click();", down_btn)
            img = self._get_downloaded_file()
            self.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            self.sleep(0.5)
            return img

        def _get_text(element: WebElement, get_markdown: bool):
            elem = element.find_element(By.CSS_SELECTOR, ".markdown")
            inner_text = elem.text.strip()
            if inner_text == "":
                return None
            if not get_markdown:
                return inner_text
            element.find_element(By.CSS_SELECTOR, 'button[aria-label="Copy response"]').click()
            self.sleep(0.5)
            return pyperclip.paste()

        wait = WebDriverWait(self.driver, 20)

        responses = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".agent-turn"))
        )

        if not responses:
            raise TimeoutException("No responses found in the chat.")

        last_response = responses[-1]

        try:
            text_content = _get_text(last_response, get_markdown)
        except NoSuchElementException:
            text_content = None

        try:
            img = _get_img(last_response)
        except NoSuchElementException:
            img = None

        if text_content is None and img is None:
            raise RuntimeError("Response contained neither text nor image.")

        return Response(text=text_content, image=img)

    def get_state(self) -> State:
        if self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="stop-button"]'):
            return State.GENERATING

        send_btns = self.driver.find_elements(
            By.CSS_SELECTOR, '[data-testid="send-button"]'
        )
        if send_btns:
            if send_btns[0].get_attribute("disabled"):
                return State.UPLOADING
            return State.TYPING

        return State.IDLE

    def _goto_model(self, model, delay=SHORT_WAIT):
        self.driver.find_element(
            By.CSS_SELECTOR, 'header button[aria-label^="Model selector"]'
        ).click()
        self.sleep(0.5)
        self.driver.find_element(
            By.CSS_SELECTOR, f'div[data-testid="model-switcher-{model}"]'
        ).click()
        self.sleep(delay)

        return self

    def goto_gpt4o(self, delay=SHORT_WAIT):
        raise NotImplementedError("Not implemented yet")

    def goto_o3(self, delay=SHORT_WAIT):
        raise NotImplementedError("Not implemented yet")

    def turn_on_thinking(self, delay=SHORT_WAIT):
        raise NotImplementedError("Not implemented yet")

    def turn_off_thinking(self, delay=SHORT_WAIT):
        raise NotImplementedError("Not implemented yet")

    def turn_on_auto_model(self, delay=SHORT_WAIT):
        raise NotImplementedError("Not implemented yet")
