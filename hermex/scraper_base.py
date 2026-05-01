import random
import re
import subprocess
import time
from abc import ABC, abstractmethod
from pathlib import Path
from tempfile import TemporaryDirectory

import undetected_chromedriver as uc
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from hermex.config import LONG_WAIT, SHORT_WAIT, data_dir
from hermex.models import Response, State
from hermex.utils import get_user_agent


def _detect_chrome_version() -> int:
    chrome = uc.find_chrome_executable()
    out = subprocess.check_output([chrome, "--version"], text=True)
    return int(re.search(r"(\d+)\.", out).group(1))


class Scraper(ABC):
    """
    Abstract base class for LLM chatbot scrapers.

    Manages the Chrome browser lifecycle, simulated typing, file downloads,
    and state polling. Subclasses implement the platform-specific DOM interactions
    for a particular chatbot (e.g. Gemini, ChatGPT).

    Use `Scraper.setup()` once to establish a persistent login session, then
    instantiate the subclass directly for subsequent runs.
    """

    _state_error_tolerance = (
        20  # seconds of consecutive state-detection failures before giving up
    )

    def __init__(
        self,
        chrome_version=None,
        download_dir=Path("."),
        headless=False,
        typing_delay=0.025,
        disable_web_security=True,
        data_dir=data_dir,
    ):
        """
        :param chrome_version: Chrome major version number. Defaults to auto-detecting
            the installed Chrome version.
        :param download_dir: Directory where downloaded files (e.g. generated images)
            are saved.
        :param headless: Run the browser without a visible window.
        :param typing_delay: Seconds between each keystroke when typing
            character-by-character.
        :param disable_web_security: Pass --disable-web-security to Chrome. Needed for
            some scrapers (e.g. ChatGPT, Gemini) but triggers bot detection on stricter
            sites — set False for those.
        :param data_dir: Root directory where Hermex stores its data. Defaults to the
            platform-appropriate data directory. Browser profiles are stored as
            subdirectories within this path (e.g. data_dir/chrome_profile/).
        """
        self.browser_profile_dir = Path(data_dir) / "chrome_profile"
        self.chrome_version = chrome_version or _detect_chrome_version()
        self.disable_web_security = disable_web_security
        self._temp_dir = TemporaryDirectory()
        self._selenium_download_dir = Path(self._temp_dir.name)
        self.download_dir = Path(download_dir)
        self.headless = headless
        self.driver = None
        self.typing_delay = typing_delay
        self.is_logged_in = False

        self.download_dir.mkdir(parents=True, exist_ok=True)

    def _initialize_driver(self):
        """Initialize and configure the Chrome driver"""
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument(f"--user-data-dir={self.browser_profile_dir}")
        options.add_argument("--enable-javascript")
        options.add_argument("--enable-cookies")
        options.add_argument("--no-sandbox")
        if self.disable_web_security:
            options.add_argument("--disable-web-security")
            options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-features=IsolateOrigins,site-per-process")

        options.add_argument(f"--user-agent={get_user_agent(self.chrome_version)}")

        options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": str(self._selenium_download_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False,
            },
        )

        if self.headless:
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")

        # Create the undetected ChromeDriver with version matching your browser
        self.driver = uc.Chrome(
            options=options, use_subprocess=True, version_main=self.chrome_version
        )
        return self

    def open_url(self, url=None, timeout=30):
        """
        Open a URL in the browser and wait for the page to be ready.

        :param url: URL to navigate to.
        :param timeout: Maximum seconds to wait for the page to be ready before raising
            TimeoutException.
        """
        if not self.driver:
            self._initialize_driver()

        self.driver.get(url)
        self.wait_for_page_load(timeout)

        return self

    @abstractmethod
    def wait_for_page_load(self, timeout: float = 30) -> None:
        """Wait until the page is ready to interact with."""

    @abstractmethod
    def send_message(
        self,
        message: str,
        submit: bool = True,
        images: list[str | Path] = None,
        paste: bool = False,
        fake_typing: bool = True,
        typing_delay: float = None,
    ) -> "Scraper":
        """
        Input a message into the chat, optionally attaching images.

        :param message: Text to send.
        :param submit: Whether to press Enter after composing the message.
        :param images: List of image file paths to attach before the message.
        :param paste: If True, paste the message instead of typing it character by
                      character. Useful for long messages where typing is too slow.
        :param fake_typing: When paste=True, type dummy text first to avoid bot
                            detection, then replace it with the real message.
        :param typing_delay: Seconds between each keystroke. Overrides the
                             instance-level default set in the constructor for this call
                             only.
        """

    @abstractmethod
    def get_last_response(
        self, get_markdown: bool = False, remove_watermark: bool = False
    ) -> "Response":
        """
        Retrieve the last response from the chat interface.

        :param get_markdown: If True, return the raw markdown source instead of plain text.
        :param remove_watermark: If True, remove the watermark from any downloaded image.
        :return: Response object with text and image fields (either may be None, but not both).
        """

    @abstractmethod
    def get_state(self) -> State:
        """
        Return the current state of the chatbot UI.

        Possible states:
        - State.IDLE: the interface is ready and waiting for input.
        - State.TYPING: the input box has content that has not been submitted yet.
        - State.UPLOADING: a file upload is in progress.
        - State.GENERATING: the model is actively generating a response.

        :return: A State value representing the current UI state.
        :raises Exception: if the state cannot be determined (e.g. expected DOM elements
            are missing). Callers that need to tolerate transient failures should use
            wait_until_idle() instead, which has built-in error tolerance.
        """

    def _wait_until_state(self, target: State, timeout: float = LONG_WAIT) -> None:
        start = time.time()
        error_since = None
        while time.time() - start < timeout:
            try:
                if self.get_state() == target:
                    return
                error_since = None
            except Exception:
                if error_since is None:
                    error_since = time.time()
                elif time.time() - error_since > self._state_error_tolerance:
                    raise
            time.sleep(1)
        raise TimeoutException(
            f"Chatbot did not reach state '{target}' within {timeout}s."
        )

    def wait_until_idle(self, timeout: float = LONG_WAIT) -> None:
        """
        Block until the chatbot has finished generating its response.

        :param timeout: Maximum seconds to wait before raising TimeoutException.
        """
        self._wait_until_state("idle", timeout)

    def query(
        self,
        message: str,
        timeout: float = LONG_WAIT,
        images: list[str | Path] = None,
        paste: bool = False,
        fake_typing: bool = True,
        typing_delay: float = None,
        get_markdown: bool = False,
        remove_watermark: bool = False,
    ) -> "Response":
        """
        Send a message, wait for the response to complete, and return it.

        :param message: Text to send.
        :param timeout: Maximum seconds to wait for the response before raising TimeoutException.
        :param images: List of image file paths to attach (platform-dependent).
        :param paste: If True, paste the message instead of typing it character by character.
                      Useful for long messages where typing is too slow.
        :param fake_typing: When paste=True, type dummy text first to avoid bot detection,
                            then replace it with the real message.
        :param typing_delay: Seconds between each keystroke. Overrides the instance-level default.
        :param get_markdown: If True, return the raw markdown source instead of plain text.
        :param remove_watermark: If True, remove the watermark from any downloaded image.
        :return: Response object with text and image fields (either may be None, but not both).
        """
        self.send_message(
            message,
            images=images,
            paste=paste,
            fake_typing=fake_typing,
            typing_delay=typing_delay,
        )
        self.wait_until_idle(timeout)
        return self.get_last_response(
            get_markdown=get_markdown, remove_watermark=remove_watermark
        )

    def _type_into(
        self,
        message: str,
        input_box: WebElement,
        typing_delay: float = None,
    ):
        delay = typing_delay if typing_delay is not None else self.typing_delay
        for char in message:
            if char == "\n":  # Handle Newline: Shift+Enter
                input_box.send_keys(Keys.SHIFT, Keys.ENTER)
            elif ord(char) > 0xFFFF:  # Handle Emojies
                self.driver.execute_script(
                    "document.execCommand('insertText', false, arguments[0]);", char
                )
            else:
                input_box.send_keys(char)
            self.sleep(delay)

        self.sleep(2)
        return self

    def _paste_into(
        self,
        message: str,
        input_box: WebElement,
        fake_typing=True,
        typing_delay: float = None,
    ):
        if fake_typing:
            self._type_into(
                "Some fake text... " * 20, input_box, typing_delay=typing_delay
            )
            self.driver.execute_script(
                "document.execCommand('selectAll', false, null);"
            )

        self.driver.execute_script(
            "document.execCommand('insertText', false, arguments[0]);", message
        )
        self.sleep(2)
        return self

    def sleep(self, t):
        """
        Sleep for approximately t seconds, with a small random jitter to appear more human-like.

        :param t: Target sleep duration in seconds.
        """
        minmax_factor = 0.2
        min_time = t - t * minmax_factor
        max_time = t + t * minmax_factor
        time.sleep(random.uniform(min_time, max_time))

        return self

    def long_wait(self):
        """Wait for the default long duration (5 minutes). Use after sending a prompt
        that triggers image generation or a slow response."""
        return self.sleep(LONG_WAIT)

    def short_wait(self):
        """Wait for the default short duration (7 seconds). Use after UI interactions
        that need a moment to settle."""
        return self.sleep(SHORT_WAIT)

    def refresh_page(self):
        """Reload the current page."""
        self.driver.refresh()
        return self

    def get_current_url(self, only_base=False):
        """
        Return the current browser URL.

        :param only_base: If True, strip query parameters and return only the base URL.
        """
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

    @classmethod
    def setup(cls):
        """
        First-time setup required before using Hermex.

        Opens a browser window so you can browse around briefly. This builds a
        browser profile that looks like a real user, which significantly reduces
        bot detection risk in subsequent automated runs. Everyone must run this
        at least once after installation.

        If you need login-gated features (e.g. image upload), log in
        during this session. Hermex will reuse the saved session in all future
        runs — repeat setup only if your session expires.

        Close the browser window when done.

        Usage:
            Gemini.setup()
        """
        print("==> Opening browser. Browse around briefly, then close the window when done.")
        scraper = cls()
        scraper.open_url()
        while True:
            try:
                scraper.driver.window_handles
                time.sleep(2)
            except Exception:
                break
        scraper.close()

    @classmethod
    def simple_query(cls, prompt, images=None, timeout=LONG_WAIT):
        """
        Open the browser, send a prompt, and return the response.

        Convenience method for one-shot scripts that don't need a persistent
        session. Opens the browser, sends the prompt, closes the browser, and
        returns the full Response object.

        :param prompt: The prompt text to send.
        :param images: Optional list of image file paths to attach.
        :param timeout: Maximum seconds to wait for the response.
        :return: Response object with text and image fields.
        """
        scraper = cls()
        response = scraper.open_url().short_wait().query(
            prompt, images=images, timeout=timeout
        )
        scraper.close()
        return response
