"""Exceptions for discogs-scraper."""


class NetworkCallFailed(Exception):
    """Raise error if reading url fails due to connectivity issues."""


class EmptyTitle(Exception):
    """Raise error if album title is empty string."""


class NoArtistForAlbum(Exception):
    """Raise if no artist was found for album title."""


class NoMarketplaceURL(Exception):
    """Raise if no marketplace url is given."""


class NoDealsAvailable(Exception):
    """Raise if there are no deals at the marketplace."""
