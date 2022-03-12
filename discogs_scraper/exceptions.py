"""Exceptions for discogs-scraper."""

class NetworkCallFailed(Exception):
    """Raise error if reading url fails due to connectivity issues."""

class EmptyTitle(Exception):
    """Raise error if album title is empty string."""

class NoArtistForAlbum(Exception):
    """Raise if no artist was found for album title."""

    

