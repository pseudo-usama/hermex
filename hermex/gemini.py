from pathlib import Path
from typing import Self

import pyperclip
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from hermex.exceptions import LoginRequiredError
from hermex.gemini_watermark_remover import gemini_remove_watermark
from hermex.models import AssistantMessage, State
from hermex.scraper_base import Scraper


class Gemini(Scraper):
    """
    Scraper for Google Gemini (gemini.google.com).

    Supports text queries, file uploads, and downloading generated images.
    Works in guest mode for basic text queries; file upload requires a
    logged-in session established via `Gemini.setup()`.

    Generated images are optionally post-processed to remove the Gemini
    watermark via `remove_watermark=True` on `query()` or `get_last_response()`.
    """

    SUPPORTED_ATTACHMENTS = { ".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".csv", ".txt", ".json" }  # fmt: skip

    def open_url(self, url="https://gemini.google.com", timeout=30):
        if "gemini.google.com" not in url:
            raise ValueError(f"Expected a gemini.google.com URL, got: {url}")
        super().open_url(url, timeout)
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
        attachments: list[str | Path] = None,
        paste: bool = False,
        fake_typing: bool = True,
        typing_delay: float = None,
        submit: bool = True,
    ) -> Self:
        wait = WebDriverWait(self.driver, 20)
        input_box = wait.until(
            EC.element_to_be_clickable((By.TAG_NAME, "rich-textarea"))
        )

        if attachments:
            if not self.is_logged_in:
                raise LoginRequiredError(
                    "File upload requires login. Run Gemini.setup() to log in."
                )
            self._upload_files(attachments)

        input_box.click()
        self.sleep(0.5)
        input_p = input_box.find_element(By.TAG_NAME, "p")

        if paste:
            self._paste_into(
                message, input_p, fake_typing=fake_typing, typing_delay=typing_delay
            )
        else:
            self._type_into(message, input_p, typing_delay=typing_delay)

        if attachments:
            self._wait_until_state(State.TYPING)

        if submit:
            input_p.send_keys("\n")

        return self

    def _upload_files(self, file_paths: list[str | Path]):
        resolved = []
        for file_path in file_paths:
            file_path = Path(file_path).resolve()
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            if file_path.suffix.lower() not in self.SUPPORTED_ATTACHMENTS:
                raise ValueError(
                    f"Unsupported file type '{file_path.suffix}'. Must be one of: {self.SUPPORTED_ATTACHMENTS}"
                )
            resolved.append(file_path)

        wait = WebDriverWait(self.driver, 10)

        # Gemini's JS calls input.click() internally when the upload menu item is clicked,
        # which would open an OS file dialog we can't control. Patch the prototype before
        # any clicks so that call is silently suppressed. The patch is restored in the
        # finally block below so it is never left active if an intermediate step fails.
        self.driver.execute_script("""
            const orig = HTMLInputElement.prototype.click;
            HTMLInputElement.prototype.click = function() {
                if (this.type === 'file') return;
                return orig.apply(this, arguments);
            };
            window.__restoreFileClick = () => { HTMLInputElement.prototype.click = orig; };
        """)

        try:
            self.driver.find_element(
                By.CSS_SELECTOR,
                '[data-node-type="input-area"] button[aria-label="Upload & tools"]',
            ).click()

            # Clicking "Upload files" creates the hidden input[name="Filedata"] and triggers .click() on it.
            # Both the maximized and narrow/mobile upload menus wrap the trigger in the same
            # <images-files-uploader data-test-id="uploader-images-files-button-advanced"> element, but the
            # visible button inside differs by layout (a mat-list-item menu item vs. a mobile mdc-button).
            # Each wrapper also holds a hidden decoy (.hidden-local-file-image-selector-button) we must not
            # click — :not() excludes it, so this resolves to the visible trigger in either layout.
            wait.until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        'images-files-uploader[data-test-id="uploader-images-files-button-advanced"] '
                        "button:not(.hidden-local-file-image-selector-button)",
                    )
                )
            ).click()

            # The input is display:none — unhide it so Selenium accepts send_keys.
            # send_keys on a file input bypasses the OS dialog entirely (ChromeDriver handles it internally).
            file_input = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'input[name="Filedata"]')
                )
            )
            self.driver.execute_script(
                "arguments[0].style.display = 'block';", file_input
            )
            file_input.send_keys("\n".join(str(p) for p in resolved))
        finally:
            # Best-effort restore. If the page/session is in a bad state the restore
            # itself may fail — swallow that so it never masks the original upload error.
            try:
                self.driver.execute_script(
                    "window.__restoreFileClick && window.__restoreFileClick();"
                )
            except WebDriverException:
                pass

    def get_last_response(
        self, get_markdown=False, remove_watermark=False
    ) -> AssistantMessage:
        def _get_img(element: WebElement):
            self.sleep(1.5)
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

        return AssistantMessage(text=text_content, image=img)

    def get_state(self) -> State:
        container = self.driver.find_element(
            By.CSS_SELECTOR, '[data-test-id="send-button-container"]'
        )
        button = container.find_element(By.CSS_SELECTOR, "gem-icon-button.send-button")
        classes = (button.get_attribute("class") or "").split()

        # While generating, the send button is swapped for a stop button (class "stop",
        # aria-label "Stop response"). Using the class avoids breaking on label localization.
        if "stop" in classes:
            return State.GENERATING

        # The "has-input" class is added whenever the input box has content. Without it,
        # the box is empty and the UI is idle.
        if "has-input" not in classes:
            return State.IDLE

        # With content, the button is enabled (TYPING) unless an upload is in progress,
        # in which case it is disabled (aria-disabled="true") until the upload completes.
        if button.get_attribute("aria-disabled") == "true":
            return State.UPLOADING

        return State.TYPING
