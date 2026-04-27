from pathlib import Path
from shutil import move as move_file
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement

from janus.scraper_base import Scraper
from janus.models import Response
from janus.config import SHORT_WAIT


class ChatGPT(Scraper):
    def open_url(self, url="https://chatgpt.com"):
        super().open_url(url)
        return self

    def send_message(self,
                     message,
                     submit=True,
                     images: list[str | Path] = None,
                     paste=False,
                     fake_typing=True,
                     typing_delay: float = None):
        if images:
            raise NotImplementedError("Image upload not implemented for ChatGPT.")

        wait = WebDriverWait(self.driver, 20)
        input_box = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[contenteditable="true"]'))
        )
        input_box.click()
        self.sleep(0.5)

        if paste:
            self._paste_into(message, input_box, submit=submit, fake_typing=fake_typing, typing_delay=typing_delay)
        else:
            self._type_into(message, input_box, submit=submit, typing_delay=typing_delay)

        return self

    def get_last_response(self,
                          get_markdown=False,
                          remove_watermark=False) -> Response:
        if get_markdown:
            raise NotImplementedError("get_markdown is not supported for ChatGPT yet.")
        if remove_watermark:
            raise NotImplementedError("remove_watermark is not supported for ChatGPT yet.")

        def _get_img(element: WebElement):
            image_elems = element.find_elements(By.CSS_SELECTOR, "img")
            if not image_elems:
                raise NoSuchElementException("No image element in this response.")
            image_elems[0].click()
            self.sleep(20)
            down_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "header.grid > div:nth-of-type(2) button:nth-of-type(4)")))
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
        except NoSuchElementException:
            text_content = None

        try:
            img = _get_img(last_response)
        except NoSuchElementException:
            img = None

        if text_content is None and img is None:
            raise RuntimeError("Response contained neither text nor image.")

        return Response(text=text_content, image=img)

    def _goto_model(self, model, delay=SHORT_WAIT):
        self.driver.find_element(By.CSS_SELECTOR, f'header button[aria-label^="Model selector"]').click()
        self.sleep(0.5)
        self.driver.find_element(By.CSS_SELECTOR, f'div[data-testid="model-switcher-{model}"]').click()
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
