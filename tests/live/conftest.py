"""Shared browser fixtures for the live suites.

Every logged-in fixture builds its profile under the same `data_dir/chrome_profile/`,
and two Chrome instances cannot share a `--user-data-dir`. Session-scoped fixtures stay
alive until the pytest session ends, so no single invocation may touch two logged-in
suites — `pytest tests/live/` would hold Gemini's and ChatGPT's at once and the second
launch would fail. The guest fixtures are exempt: each gets a throwaway profile under a
pytest temp dir, so a guest session can run alongside a logged-in one.
"""

import warnings
from collections.abc import Iterator

import pytest

from hermex import ChatGPT, Gemini


@pytest.fixture(scope="session")
def gemini(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Gemini]:
    """One logged-in browser session shared by every Gemini test.

    Downloads go to a pytest temp dir so generated images never land in the repo.
    """
    bot = Gemini(download_dir=tmp_path_factory.mktemp("downloads"))
    try:
        bot.open_url()
        yield bot
    finally:
        # In the finally block because open_url() can raise (captcha, network, a
        # driver/Chrome version mismatch) after the browser is already up, and a
        # fixture that dies before yielding never runs its teardown otherwise —
        # leaving an orphaned Chrome holding the profile lock for the next run.
        bot.close()


@pytest.fixture(scope="session")
def chatgpt(tmp_path_factory: pytest.TempPathFactory) -> Iterator[ChatGPT]:
    """One logged-in browser session shared by every logged-in ChatGPT test."""
    bot = ChatGPT(download_dir=tmp_path_factory.mktemp("downloads"))
    try:
        bot.open_url()
        yield bot
    finally:
        bot.close()


@pytest.fixture(scope="session")
def chatgpt_guest(tmp_path_factory: pytest.TempPathFactory) -> Iterator[ChatGPT]:
    """One signed-out browser session shared by every logged-out ChatGPT test.

    A fresh data_dir means a fresh Chrome profile with no OpenAI cookies, which is how
    we get a guest session without touching the real profile.
    """
    data_dir = tmp_path_factory.mktemp("guest_profile")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)  # setup() has not been run
        bot = ChatGPT(data_dir=data_dir, download_dir=data_dir)
    try:
        bot.open_url()
        yield bot
    finally:
        bot.close()
