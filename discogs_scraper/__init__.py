"""Discogs Scraper Package."""

from .core import DiscogsScraper  # noqa: F401
from .exceptions import NetworkCallFailed, EmptyTitle, NoArtistForAlbum, \
    NoMarketplaceURL, NoDealsAvailable  # noqa: F401
