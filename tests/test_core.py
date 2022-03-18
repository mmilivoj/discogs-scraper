import os
import time 

import pytest
from pathlib import Path

from .context import discogs_scraper



@pytest.fixture
def release():
    return discogs_scraper.core.DiscogsScraper("Kill em all", "Metallica")


def test_album_title_is_empty_string():
    """Test if EmptyTitle is raised for an empty string argument."""
    with pytest.raises(discogs_scraper.exceptions.EmptyTitle):
        release = discogs_scraper.core.DiscogsScraper("")


@pytest.mark.skip(reason="Not applicable to GitHub's Actions. (ubuntu)")
def test_searching_without_internet():
    """Test if exception is raised when no internet connection."""
    # os commands are only applied to MacOS.
    os.system("networksetup -setairportpower airport off")  # Disable Wifi
    with pytest.raises(discogs_scraper.exceptions.NetworkCallFailed):
        release = discogs_scraper.core.DiscogsScraper("The Dark Side of the Moon")
    os.system("networksetup -setairportpower airport on")  # Enable Wifi
    # Wait five seconds unitl internet connection is established for subsequent tests.
    time.sleep(5)


def test_album_with_no_artist():
    """Test if exception is raised for non-existing Album-Artist combination."""
    with pytest.raises(discogs_scraper.exceptions.NoArtistForAlbum):
        release = discogs_scraper.core.DiscogsScraper("The Dark Side of the Moon", "Metallica")
        master_url = release.find_master()


def test_find_master(release):
    release.find_master()
    marketplace_url = release.marketplace_url
    assert marketplace_url == "https://www.discogs.com/sell/list?sort=condition%2Cdesc&limit=250&master_id=6387&ev=mb&format=Vinyl"


def test_extract(release):
    release.find_master()
    release.extract()
    dir_path = Path(os.getcwd())
    assert os.path.exists(dir_path / "raw.csv")
    os.remove(dir_path / "raw.csv")
