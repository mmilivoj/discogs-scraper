import os
import time 

import pytest

from .context import discogs_scraper


def test_album_title_is_empty_string():
    """Test if EmptyTitle is raised for an empty string argument."""
    with pytest.raises(discogs_scraper.exceptions.EmptyTitle):
        release = discogs_scraper.core.DiscogsScraper("")


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