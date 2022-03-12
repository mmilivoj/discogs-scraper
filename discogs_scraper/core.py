"""Discogs marketplace scraper."""
import time
import re

import requests
from bs4 import BeautifulSoup
import pandas as pd

from .exceptions import NetworkCallFailed, EmptyTitle, NoArtistForAlbum


class DiscogsScraper:
    """Scrape vinyl informtion from """

    def __init__(self, album: str, artist: str = "") -> None:
        """Create release object.

        Args:
            artist (str, optional): Artist/Band of th album. Helpful if multiple
            album (str): title of the album to be scraped.
            artists have the same album title. Defaults to "".
        """
        self.base_url = "https://www.discogs.com"
        self.sort = "sort=condition%2Cdesc&limit=250"
        self.phonogram = "format=Vinyl"
        self.album = "-".join(album.split()).lower()
        self.artist = "-".join(artist.split()).lower()
        self.master_url = f"{self.base_url}/search/?q={self.album}&type=master"
        self.marketplace_url = ""

        if not self.album:
            raise EmptyTitle("Received empty album title. Please specify a title.")
        try:
            time.sleep(1)
            res = requests.get(self.master_url)
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
            self.marketplace_url = f"{self.base_url}/sell/list?{self.sort}&master_id={master_id}&ev=mb&{self.phonogram}"
        except UnboundLocalError:
            # UnboundLocalError thrown, if master_id was not assigned a value.
            # Happens when a combination of artist and album is specified, that is not available on Discogs.com
            album = self.album.replace("-", " ").title()
            artist = self.artist.title()
            raise NoArtistForAlbum(f'Could not found "{album}" by {artist}.')

    def extract(self):
        """Extract all releases from marketplace."""

        data_set = []
        page_nr = 1
        next_page = True
        while next_page:
            html_doc = requests.get(self.marketplace_url + f"&page={page_nr}").text
            marketplace = BeautifulSoup(html_doc, "lxml")
            releases = marketplace.find_all("tr", attrs={"class": "shortcut_navigable"})
            if not releases:
                return "No items for sale."
            for release in releases:
                media_condition = release.find(
                    "p", attrs={"class": "item_condition"}
                ).find_all("span")[2]
                if (media_condition is None) or (media_condition == "Good Plus (G+)"):
                    next_page = False
                    continue
                title = release.find("a", class_="item_description_title")
                selling_page = release.find("a", class_="item_description_title")["href"]
                have = release.find(class_=re.compile(r"have_indicator.*?"))
                want = release.find(class_=re.compile(r"want_indicator.*?"))
                try:
                    star_rating = release.find("span", class_="star_rating").parent.find(
                        "strong"
                    )
                except AttributeError:
                    # no parent
                    star_rating = ""
                try:
                    number_of_ratings = release.find(
                        "span", attrs={"class": "star_rating"}
                    ).find_next_sibling("a")
                except AttributeError:
                    number_of_ratings = ""
                total_price_in_euro = release.find("span", class_="converted_price")
                release_page = (
                    self.base_url
                    + release.find("a", attrs={"class": "item_release_link"})["href"]
                )

                raw_data = [
                    title,
                    have,
                    want,
                    star_rating,
                    number_of_ratings,
                    total_price_in_euro,
                    media_condition,
                    release_page,
                    selling_page,
                ]

                keys = [
                    "title",
                    "have",
                    "want",
                    "star_rating",
                    "number_of_ratings",
                    "total_price_in_euro",
                    "media_condition",
                    "release_page",
                    "selling_page",
                ]

                values = []

                for item in raw_data:
                    if item is not None:
                        try:
                            values.append(item.text.strip().replace(",", "."))
                        except AttributeError:
                            values.append(item)
                    else:
                        values.append("")

                new_dictionary = dict(zip(keys, values))
                data_set.append(new_dictionary)
            page_nr += 1
            # Check if next page is unavailable. If so, stop scraping.
            if marketplace.find("a", class_="pagination_next") is None:
                next_page = False

        releases_df = pd.DataFrame(data_set)
        releases_df.to_csv("raw.csv", index=False)
