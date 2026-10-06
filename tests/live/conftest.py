from collections.abc import Iterator

import pytest

from hermex import Gemini


@pytest.fixture(scope="session")
def gemini(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Gemini]:
    """One browser session shared by every test in this directory.

    Downloads go to a pytest temp dir so generated images never land in the repo.
    """
    bot = Gemini(download_dir=tmp_path_factory.mktemp("downloads"))
    bot.open_url()
    yield bot
    bot.close()
