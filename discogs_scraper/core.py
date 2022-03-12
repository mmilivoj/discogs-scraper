"""Discogs marketplace scraper."""
import requests
import time
import re

from bs4 import BeautifulSoup

from exceptions import NetworkCallFailed, EmptyTitle, NoArtistForAlbum


class DiscogsScraper:
    """Scrape vinyl informtion from """
    
    def __init__(self, album: str, artist: str = "") -> None:
        """Create release object.

        Args:
            artist (str, optional): Artist/Band of th album. Helpful if multiple
            album (str): title of the album to be scraped.
            artists have the same album title. Defaults to "".
        """
        self.album = "-".join(album.split()).lower()
        self.artist = "-".join(artist.split()).lower()
        self.url = f"https://www.discogs.com/search/?q={self.album}&type=master"
        if not self.album:
            # raise exception if 
            raise EmptyTitleError("Received empty album title. Please specify a title.")
        try:
            time.sleep(1)
            res = requests.get(self.url)
            res.raise_for_status()
        except requests.exceptions.RequestException as err:
            if isinstance(err, requests.exceptions.ConnectionError):
                raise NetworkCallFailed("Failed to establish internet connection.")
        
        self.master_releases_tree = BeautifulSoup(res.text, "lxml")
    
    def find_master(self):
        """Find master release for specified album [and artist optionally]."""

        master_releases = self.master_releases_tree.find_all(
        "div", attrs={"data-object-type": "master release"}
        )
        m_id_regex = re.compile(r"\d+")  # search schema for id of master release
        if not self.artist:
            # No Artist specified
            master_url = master_releases[0].find("a")["href"]
            master_id = m_id_regex.search(master_url).group(0)
        else:
            # Artist specified
            for master_release in master_releases:
                master_url = master_release.find("a")["href"].lower()
                if self.album in master_url and self.artist in master_url:
                    master_id = m_id_regex.search(master_url).group(0)
                    break
        try:
            marketplace_url = f"https://www.discogs.com/sell/list?sort=condition%2Cdesc&limit=250&master_id={master_id}&ev=mb&format=Vinyl"
            return marketplace_url
        except UnboundLocalError:
            # UnboundLocalError thrown, if master_id was not assigned a value.
            # Happens when a combination of artist and album is specified, that is not available on Discogs.com
            album = self.album.replace("-", " ").title()
            artist = self.artist.title()
            raise NoArtistForAlbum(f'Could not found "{album}" authorized by {artist}.')

