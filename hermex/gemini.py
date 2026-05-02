from pathlib import Path

import pyperclip
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from hermex.config import SUPPORTED_IMAGE_EXTENSIONS
from hermex.exceptions import LoginRequiredError
from hermex.gemini_watermark_remover import gemini_remove_watermark
from hermex.models import Response, State
from hermex.scraper_base import Scraper


class Gemini(Scraper):
    """
    Scraper for Google Gemini (gemini.google.com).

    Supports text queries, image uploads, and downloading generated images.
    Works in guest mode for basic text queries; image upload requires a
    logged-in session established via `Gemini.setup()`.

    Generated images are optionally post-processed to remove the Gemini
    watermark via `remove_watermark=True` on `query()` or `get_last_response()`.
    """

    def open_url(self, url="https://gemini.google.com", timeout=30):
        if "gemini.google.com" not in url:
            raise ValueError(f"Expected a gemini.google.com URL, got: {url}")
        super().open_url(url, timeout)
        self._detect_login()
        return self

    def wait_for_page_load(self, timeout: float = 30) -> None:
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "rich-textarea"))
        )

    def _detect_login(self):
        try:
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'a[aria-label="Sign in"]')
                )
            )
            self.is_logged_in = False
        except TimeoutException:
            self.is_logged_in = True

    def send_message(
        self,
        message: str,
        submit=True,
        images: list[str | Path] = None,
        paste=False,
        fake_typing=True,
        typing_delay: float = None,
    ):
        wait = WebDriverWait(self.driver, 20)
        input_box = wait.until(
            EC.element_to_be_clickable((By.TAG_NAME, "rich-textarea"))
        )

        if images:
            if not self.is_logged_in:
                raise LoginRequiredError(
                    "Image upload requires login. Run Gemini.setup() to log in."
                )
            self._upload_imgs(images)

        input_box.click()
        self.sleep(0.5)
        input_p = input_box.find_element(By.TAG_NAME, "p")

        if paste:
            self._paste_into(
                message, input_p, fake_typing=fake_typing, typing_delay=typing_delay
            )
        else:
            self._type_into(message, input_p, typing_delay=typing_delay)

        if images:
            self._wait_until_state(State.TYPING)

        if submit:
            input_p.send_keys("\n")

        return self

    def get_last_response(self, get_markdown=False, remove_watermark=False) -> Response:
        def _get_img(element: WebElement):
            element.find_element(
                By.TAG_NAME, "download-generated-image-button"
            ).find_element(By.TAG_NAME, "button").click()
            img = self._get_downloaded_file()
            return img

        def _get_text(element: WebElement, get_markdown):
            elem = element.find_element(By.CSS_SELECTOR, ".markdown")
            inner_text = elem.text.strip()
            if inner_text == "":
                return None
            if not get_markdown:
                return inner_text
            element.find_element(By.TAG_NAME, "copy-button").click()
            self.sleep(0.5)
            return pyperclip.paste()

        wait = WebDriverWait(self.driver, 20)
        responses = wait.until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "model-response"))
        )
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

        if remove_watermark and img is not None:
            gemini_remove_watermark(str(img), str(img))

        return Response(text=text_content, image=img)

    def _upload_imgs(self, image_paths: list[str | Path]):
        resolved = []
        for image_path in image_paths:
            image_path = Path(image_path).resolve()
            if image_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
                raise ValueError(
                    f"Unsupported file type '{image_path.suffix}'. Must be one of: {SUPPORTED_IMAGE_EXTENSIONS}"
                )
            resolved.append(image_path)

        wait = WebDriverWait(self.driver, 10)

        # Gemini's JS calls input.click() internally when the upload menu item is clicked,
        # which would open an OS file dialog we can't control. Patch the prototype before
        # any clicks so that call is silently suppressed. The patch is restored after upload.
        self.driver.execute_script("""
            const orig = HTMLInputElement.prototype.click;
            HTMLInputElement.prototype.click = function() {
                if (this.type === 'file') return;
                return orig.apply(this, arguments);
            };
            window.__restoreFileClick = () => { HTMLInputElement.prototype.click = orig; };
        """)

        self.driver.find_element(
            By.CSS_SELECTOR,
            '[data-node-type="input-area"] button[aria-label="Open upload file menu"]',
        ).click()

        # Clicking "Upload files" creates the hidden input[name="Filedata"] and triggers .click() on it.
        wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '[data-test-id="local-images-files-uploader-button"]')
            )
        ).click()

        # The input is display:none — unhide it so Selenium accepts send_keys.
        # send_keys on a file input bypasses the OS dialog entirely (ChromeDriver handles it internally).
        file_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="Filedata"]'))
        )
        self.driver.execute_script("arguments[0].style.display = 'block';", file_input)
        file_input.send_keys("\n".join(str(p) for p in resolved))
        self.driver.execute_script(
            "window.__restoreFileClick && window.__restoreFileClick();"
        )

    def get_state(self) -> State:
        input_area = self.driver.find_element(
            By.CSS_SELECTOR, '[data-node-type="input-area"]'
        )

        send_stop = input_area.find_element(
            By.CSS_SELECTOR, '[aria-label="Send message"], [aria-label="Stop response"]'
        )
        # While generating, Gemini swaps the send button's aria-label to "Stop response".
        if send_stop.get_attribute("aria-label") == "Stop response":
            return State.GENERATING

        # During upload, the send button is disabled (aria-disabled="true") but still
        # focusable (tabindex="0"). In IDLE the button is also disabled but tabindex="-1",
        # so tabindex is the only signal that distinguishes the two states.
        if (
            send_stop.get_attribute("aria-disabled") == "true"
            and send_stop.get_attribute("tabindex") == "0"
        ):
            return State.UPLOADING

        # When the input has content, Gemini hides the mic button to reveal the send button.
        mic = input_area.find_element(By.CSS_SELECTOR, '[aria-label="Microphone"]')
        container = mic.find_element(
            By.XPATH, 'ancestor::*[contains(@class, "mic-button-container")]'
        )
        if "hidden" in container.get_attribute("class"):
            return State.TYPING

        return State.IDLE
