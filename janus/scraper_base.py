import re
import sys
import time
import random
import subprocess
from pathlib import Path
from abc import ABC, abstractmethod
from tempfile import TemporaryDirectory
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webelement import WebElement

from janus.adaptive_delay import wait as long_sleep
from janus.config import data_dir, LONG_WAIT, SHORT_WAIT
from janus.utils import get_user_agent


def _detect_chrome_version() -> int:
    chrome = uc.find_chrome_executable()
    out = subprocess.check_output([chrome, "--version"], text=True)
    return int(re.search(r"(\d+)\.", out).group(1))


class Scraper(ABC):
    _state_error_tolerance = 20  # seconds of consecutive state-detection failures before giving up

    def __init__(self,
                 chrome_version=None,
                 download_dir=Path("."),
                 headless=False,
                 typing_delay=0.025,
                 disable_web_security=True,
                 data_dir=data_dir):
        """
        :param chrome_version: Chrome major version number. Defaults to auto-detecting the
            installed Chrome version.
        :param download_dir: Directory where downloaded files (e.g. generated images) are saved.
        :param headless: Run the browser without a visible window.
        :param typing_delay: Seconds between each keystroke when typing character-by-character.
        :param disable_web_security: Pass --disable-web-security to Chrome. Needed for some
            scrapers (e.g. ChatGPT, Gemini) but triggers bot detection on stricter sites — set
            False for those.
        :param data_dir: Root directory where Janus stores its data. Defaults to the
            platform-appropriate data directory. Browser profiles are stored as subdirectories
            within this path (e.g. data_dir/chrome_profile/).
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
            self._initialize_driver()

        self.driver.get(url)

        return self

    @abstractmethod
    def send_message(self,
                     message: str,
                     submit: bool = True,
                     images: list[str | Path] = None,
                     paste: bool = False,
                     fake_typing: bool = True,
                     typing_delay: float = None) -> "Scraper":
        """
        Input a message into the chat, optionally attaching images.

        :param message: Text to send.
        :param submit: Whether to press Enter after composing the message.
        :param images: List of image file paths to attach before the message.
        :param paste: If True, paste the message instead of typing it character by character.
                      Useful for long messages where typing is too slow.
        :param fake_typing: When paste=True, type dummy text first to avoid bot detection,
                            then replace it with the real message.
        :param typing_delay: Seconds between each keystroke. Overrides the instance-level
                             default set in the constructor for this call only.
        """

    @abstractmethod
    def get_last_response(self,
                          get_markdown: bool = False,
                          remove_watermark: bool = False) -> tuple[str | None, Path | None]:
        """
        Retrieve the last response from the chat interface.

        :param get_markdown: If True, return the raw markdown source instead of plain text.
        :param remove_watermark: If True, remove the watermark from any downloaded image.
        :return: Tuple of (text_content, image_path), either may be None.
        """

    @abstractmethod
    def _get_chatbot_state(self) -> str:
        """
        Return the current state of the chatbot UI.
        Subclasses must return one of: 'generating', 'typing', 'idle'.
        """

    def wait_until_idle(self, timeout: float = LONG_WAIT) -> None:
        """
        Block until the chatbot has finished generating its response.

        :param timeout: Maximum seconds to wait before raising TimeoutException.
        """
        start = time.time()
        error_since = None
        while time.time() - start < timeout:
            try:
                if self._get_chatbot_state() == 'idle':
                    return
                error_since = None
            except Exception as e:
                if error_since is None:
                    error_since = time.time()
                elif time.time() - error_since > self._state_error_tolerance:
                    raise
            time.sleep(1)
        raise TimeoutException(f"Chatbot did not become idle within {timeout}s.")

    def query(self,
              message: str,
              timeout: float = LONG_WAIT,
              images: list[str | Path] = None,
              paste: bool = False,
              fake_typing: bool = True,
              typing_delay: float = None,
              get_markdown: bool = False,
              remove_watermark: bool = False) -> tuple[str | None, Path | None]:
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
        :return: Tuple of (text_content, image_path), either may be None.
        """
        self.send_message(message,
                          images=images,
                          paste=paste,
                          fake_typing=fake_typing,
                          typing_delay=typing_delay)
        self.wait_until_idle(timeout)
        text, image = self.get_last_response(get_markdown=get_markdown,
                                             remove_watermark=remove_watermark)
        return text, image

    def _type_into(self, message: str, input_box: WebElement, submit=True, typing_delay: float = None):
        delay = typing_delay if typing_delay is not None else self.typing_delay
        for char in message:
            if char == '\n':            # Handle Newline: Shift+Enter
                input_box.send_keys(Keys.SHIFT, Keys.ENTER)
            elif ord(char) > 0xFFFF:    # Handle Emojies
                self.driver.execute_script("document.execCommand('insertText', false, arguments[0]);", char)
            else:
                input_box.send_keys(char)
            self.sleep(delay)

        self.sleep(2)

        if submit:
            input_box.send_keys("\n")

        return self

    def _paste_into(self, message: str, input_box: WebElement, submit=True, fake_typing=True, typing_delay: float = None):
        if fake_typing:
            self._type_into("Some fake text... " * 20, input_box, submit=False, typing_delay=typing_delay)
            self.driver.execute_script("document.execCommand('selectAll', false, null);")

        self.driver.execute_script("document.execCommand('insertText', false, arguments[0]);", message)
        self.sleep(2)

        if submit:
            input_box.send_keys("\n")

        return self

    def _paste(self):
        self.driver.switch_to.window(self.driver.current_window_handle)
        self.driver.execute_script("window.focus();")
        if sys.platform == 'darwin':
            ActionChains(self.driver).key_down(Keys.COMMAND).send_keys('v').key_up(Keys.COMMAND).perform()
        elif sys.platform == 'win32':
            raise NotImplementedError("Paste not implemented for Windows.")
        elif sys.platform.startswith('linux'):
            raise NotImplementedError("Paste not implemented for Linux.")
        else:
            raise NotImplementedError(f"Paste not implemented for OS: {sys.platform}")

    def sleep(self, t):
        if t > 40:
            long_sleep(t)
            return self

        minmax_factor = 0.2
        min_time = t - t * minmax_factor
        max_time = t + t * minmax_factor
        time.sleep(random.uniform(min_time, max_time))

        return self

    def long_wait(self):
        """Wait for the default long duration (5 minutes). Use after sending a prompt that triggers image generation or a slow response."""
        return self.sleep(LONG_WAIT)

    def short_wait(self):
        """Wait for the default short duration (7 seconds). Use after UI interactions that need a moment to settle."""
        return self.sleep(SHORT_WAIT)

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

    @classmethod
    def setup(cls):
        """
        One-time setup to establish a persistent browser session.

        Opens a browser window for you to log in manually. Janus reuses this
        session in all future runs, so you only need to do this once (or when
        your session expires).

        Why this is necessary: a brand-new browser profile with no history or
        cookies is much more likely to be flagged as a bot. Logging in manually
        and briefly using the site trains the profile to look like a real user,
        which significantly reduces detection risk in subsequent automated runs.

        Usage:
            Gemini.setup()
            ChatGPT.setup()
        """
        print("==> Opening browser. Please log in and browse around briefly.")
        print("==> When you're done, come back here and press Enter to close.")
        scraper = cls()
        try:
            scraper.open_url()
            input("\nPress Enter to close the browser...")
        finally:
            scraper.close()

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
        scraper = cls()
        text, _ = scraper.open_url() \
            .short_wait() \
            .send_message(prompt) \
            .sleep(wait) \
            .get_last_response()

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
            self.send_message(prompt).sleep(delay)

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
