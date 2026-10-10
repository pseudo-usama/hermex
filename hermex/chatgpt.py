from pathlib import Path
from typing import Self

import pyperclip
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from hermex.exceptions import HeadlessClipboardError, LoginRequiredError
from hermex.models import AssistantMessage, State
from hermex.scraper_base import Scraper

# Signed out, chatgpt.com serves a different frontend (its form posts to
# /unauth-mweb/conversation and carries data-logged-out), not a restyled version of the
# authed one. The composer is a plain <textarea> rather than a contenteditable
# ProseMirror div, so which one is mounted decides every other selector below — and it
# is also the most reliable way to tell the two sessions apart.
#
# The authed composer is scoped to its form, not matched by contenteditable alone:
# ChatGPT's writing block is an editable element that is *also* a
# div[contenteditable="true"], and it renders ahead of the composer in the DOM, so the
# looser selector resolved to the writing block whenever one was open and the message
# was typed into it instead of sent. Scoping by form rather than by the element's own
# attributes is deliberate — the composer div has been through `id="prompt-textarea"`
# and now carries only `data-composer-markdown`, while the writing block sits outside
# the composer form either way. If this hook is renamed in turn, open_url() fails at
# wait_for_page_load(), which is loud; matching the writing block by accident is silent.
_AUTHED_INPUT = 'form[data-chatgpt-composer] div[contenteditable="true"]'
_GUEST_INPUT = "textarea#mobile-composer-prompt"
_GUEST_SUBMIT = "button[data-composer-submit]"


class ChatGPT(Scraper):
    """
    Scraper for ChatGPT (chatgpt.com).

    Supports text queries, file uploads, and downloading generated images.

    Only text queries work without login. OpenAI gates file upload and image
    generation behind a login on the signed-out site, so both require a session
    established via `ChatGPT.setup()`. Passing `attachments` in guest mode
    raises `LoginRequiredError`.
    """

    SUPPORTED_ATTACHMENTS = { ".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".csv", ".txt", ".json" }  # fmt: skip

    def open_url(self, url: str | None = None, timeout: float = 30) -> Self:
        url = url or "https://chatgpt.com"
        if "chatgpt.com" not in url:
            raise ValueError(f"Expected a chatgpt.com URL, got: {url}")
        super().open_url(url, timeout)
        return self

    def wait_for_page_load(self, timeout: float = 30) -> None:
        # Either composer means the page is usable. Waiting only for the authed one
        # made open_url() time out for signed-out visitors, which also meant
        # _detect_login() never got to run.
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, f"{_AUTHED_INPUT}, {_GUEST_INPUT}")
            )
        )

    def _is_guest_composer(self) -> bool:
        """True when the signed-out composer is the one mounted."""
        return bool(self.driver.find_elements(By.CSS_SELECTOR, _GUEST_INPUT))

    def _detect_login(self) -> None:
        # The signed-out composer is a definitive tell and needs no wait, since
        # wait_for_page_load() has already resolved one composer or the other.
        if self._is_guest_composer():
            self.is_logged_in = False
            return

        # The authed composer may still be served to a signed-out visitor, so fall
        # back to looking for the sign-in button before concluding we have a session.
        try:
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'button[data-testid="login-button"]')
                )
            )
            self.is_logged_in = False
        except TimeoutException:
            self.is_logged_in = True

    def send_message(
        self,
        message: str,
        attachments: list[str | Path] | None = None,
        paste: bool = False,
        fake_typing: bool = True,
        typing_delay: float | None = None,
        submit: bool = True,
    ) -> Self:
        guest = self._is_guest_composer()

        if attachments:
            self._upload_files(attachments)

        wait = WebDriverWait(self.driver, 20)
        input_box = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, _GUEST_INPUT if guest else _AUTHED_INPUT)
            )
        )
        self._focus(input_box)
        self.sleep(0.5)

        if paste:
            self._paste_into(
                message, input_box, fake_typing=fake_typing, typing_delay=typing_delay
            )
        else:
            self._type_into(message, input_box, typing_delay=typing_delay)

        if attachments:
            self._wait_until_state(State.TYPING)

        if submit:
            if guest:
                # Enter in a <textarea> inserts a newline rather than submitting, so
                # the guest composer is submitted through its own button.
                self.driver.find_element(By.CSS_SELECTOR, _GUEST_SUBMIT).click()
            else:
                input_box.send_keys("\n")

        return self

    def _upload_files(self, file_paths: list[str | Path]) -> None:
        # Guarded here rather than in send_message() so a direct call is covered too.
        if self._is_guest_composer():
            raise LoginRequiredError(
                "File upload requires login. The signed-out composer accepts images "
                "only and OpenAI gates its attach menu behind a login. Run "
                "ChatGPT.setup() to log in."
            )

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

        # The input was renamed #upload-photos -> #upload-files; match either, since
        # the two ids cannot both be the composer's file input.
        file_input = self.driver.find_element(
            By.CSS_SELECTOR, "#upload-files, #upload-photos"
        )
        # It is a persistent element, so restore its original display afterward
        # instead of leaving our override on the DOM for the whole session.
        original_display = self.driver.execute_script(
            "return arguments[0].style.display;", file_input
        )
        self.driver.execute_script("arguments[0].style.display = 'block';", file_input)
        try:
            file_input.send_keys("\n".join(str(p) for p in resolved))
        finally:
            self.driver.execute_script(
                "arguments[0].style.display = arguments[1];",
                file_input,
                original_display,
            )

    def get_last_response(
        self, get_markdown: bool = False, remove_watermark: bool = False
    ) -> AssistantMessage:
        # ChatGPT does not watermark generated images, so remove_watermark is a no-op.

        if get_markdown and self.headless:
            raise HeadlessClipboardError(
                "get_markdown=True reads the response via the 'Copy response' "
                "button and the OS clipboard, which Chrome disables in headless "
                "mode. Use get_markdown=False, or run with headless=False."
            )

        guest = self._is_guest_composer()
        wait = WebDriverWait(self.driver, 20)

        # The signed-out build renders the transcript as an <ol> of <li> turns tagged by
        # role, with the response body in [data-assistant-markdown] rather than
        # .markdown. Completed turns there also carry data-message-complete, so
        # requiring it keeps a partially streamed response from being read as the final
        # one; the authed build exposes no equivalent marker.
        if guest:
            turn_selector = 'li[data-message-role="assistant"][data-message-complete]'
            body_selector = "[data-assistant-markdown]"
        else:
            turn_selector = ".agent-turn"
            body_selector = ".markdown"

        def _get_img(element: WebElement):
            try:
                image_elems = WebDriverWait(self.driver, 5).until(
                    lambda _: element.find_elements(
                        By.CSS_SELECTOR, '[class*="imagegen-image"] img'
                    )
                )
            except TimeoutException:
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
            elem = element.find_element(By.CSS_SELECTOR, body_selector)
            inner_text = elem.text.strip()
            if inner_text == "":
                return None
            if not get_markdown:
                return inner_text
            # Both builds label it the same way, so this needs no branch.
            copy_btn = element.find_element(
                By.CSS_SELECTOR, 'button[aria-label="Copy response"]'
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", copy_btn
            )
            # ChatGPT's message-action row sometimes overlaps a same-sized sibling
            # element, which fails WebElement.click()'s interactability check.
            # Moving the mouse there first and clicking via ActionChains sidesteps
            # that check (a plain JS .click() doesn't trigger the copy handler).
            ActionChains(self.driver).move_to_element(copy_btn).click().perform()
            self.sleep(0.5)
            return pyperclip.paste()

        responses = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, turn_selector))
        )

        if not responses:
            raise TimeoutException("No responses found in the chat.")

        last_response = responses[-1]

        try:
            text_content = _get_text(last_response, get_markdown)
        except NoSuchElementException:
            text_content = None

        if guest:
            # Image generation is login-gated signed out, so there is never an image to
            # find and _get_img()'s 5s wait would be burned on every single call.
            img = None
        else:
            try:
                img = _get_img(last_response)
            except NoSuchElementException:
                img = None

        if text_content is None and img is None:
            raise RuntimeError("Response contained neither text nor image.")

        return AssistantMessage(text=text_content, image=img)

    def get_state(self) -> State:
        if self._is_guest_composer():
            return self._guest_state()

        # ChatGPT dropped [data-testid="send-button"] and [data-testid="stop-button"],
        # which left this returning IDLE unconditionally. The composer's trailing slot
        # now holds one of three buttons and nothing but the aria-label names them, so
        # the state is read from structure instead — a label check would break in every
        # locale but English.
        forms = self.driver.find_elements(
            By.CSS_SELECTOR, "form[data-chatgpt-composer]"
        )
        if not forms:
            # get_state() is documented as raising when the DOM isn't what we expect,
            # and _wait_until_state() already tolerates transient failures for 20s.
            # Returning IDLE here instead would mean a slow page load reads as "done".
            raise NoSuchElementException("ChatGPT composer form not found.")
        form = forms[0]

        # Unverified since the testid rewrite, but kept: it costs one lookup and an
        # extra GENERATING signal only ever errs toward waiting longer.
        if self.driver.find_elements(
            By.CSS_SELECTOR, '[data-testid="image-gen-loading-state"]'
        ):
            return State.GENERATING

        # Composing is the only state whose trailing button is a submit button.
        submit = form.find_elements(By.CSS_SELECTOR, 'button[type="submit"]')
        if submit:
            if submit[0].get_attribute("disabled"):
                return State.UPLOADING
            return State.TYPING

        # Idle is the only state showing the voice button, and the only one where
        # dictation is enabled — ChatGPT disables it while a response streams. Both are
        # required, so a signal that moves errs toward GENERATING: wait_until_idle()
        # then waits too long and eventually raises, instead of returning early onto a
        # response that is still being written.
        shows_voice = form.find_elements(
            By.CSS_SELECTOR, 'button:has(use[href*="voice-regular"])'
        )
        dictation_off = form.find_elements(
            By.CSS_SELECTOR, 'button[disabled]:has(use[href*="microphone-"])'
        )
        if shows_voice and not dictation_off:
            return State.IDLE
        return State.GENERATING

    def _guest_state(self) -> State:
        """Read the state off the signed-out composer's submit button.

        That build has no separate stop button and no upload of its own: one submit
        button stays mounted and swaps the icon inside it, so every signal is read
        from that button. UPLOADING is unreachable here because `_upload_files()`
        refuses to run in guest mode.
        """
        buttons = self.driver.find_elements(By.CSS_SELECTOR, _GUEST_SUBMIT)
        if not buttons:
            return State.IDLE
        button = buttons[0]

        # Two hidden spans inside the button un-hide in turn — the spinner between
        # submit and the first token, then the stop icon while the response streams.
        # Both mean a response is in flight; treating only the stop icon as GENERATING
        # would let wait_until_idle() return in the gap between them.
        for marker in ("[data-composer-loading-icon]", "[data-composer-stop-icon]"):
            icons = button.find_elements(By.CSS_SELECTOR, marker)
            if icons and icons[0].get_attribute("hidden") is None:
                return State.GENERATING

        # The button is always mounted, so an empty composer is reported through
        # aria-disabled rather than through the button's absence.
        if button.get_attribute("aria-disabled") == "true":
            return State.IDLE
        return State.TYPING
