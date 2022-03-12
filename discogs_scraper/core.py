"""Discogs marketplace scraper."""
import time
import re
import csv
import webbrowser
import os

import requests
from bs4 import BeautifulSoup
import pandas as pd
import warnings

from .exceptions import NetworkCallFailed, EmptyTitle, NoArtistForAlbum, NoMarketplaceURL, NoDealsAvailable

warnings.filterwarnings('ignore')


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
        self.headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "de-de",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36",  # noqa: E501
        }

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

        if not self.marketplace_url:
            raise NoMarketplaceURL("No marketplace url specified for this object.")
        data_set = []
        page_nr = 1
        next_page = True
        while next_page:
            time.sleep(1)
            html_doc = requests.get(self.marketplace_url + f"&page={page_nr}", headers=self.headers).text
            marketplace_tree = BeautifulSoup(html_doc, "lxml")
            releases = marketplace_tree.find_all("tr", attrs={"class": "shortcut_navigable"})
            if not releases:
                raise NoDealsAvailable("There are currently no deals available for your album.")
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
            if marketplace_tree.find("a", class_="pagination_next") is None:
                next_page = False

        releases_df = pd.DataFrame(data_set)
        releases_df.to_csv("raw.csv", index=False)

    @staticmethod
    def process_raw_csv() -> None:
        """Process necessary fields."""
        df = pd.read_csv("raw.csv")
        df["star_rating"] = df["star_rating"].str.replace("%", "").astype("float")
        df = df[df["number_of_ratings"].notna()]
        df["number_of_ratings"] = (
            df["number_of_ratings"]
            .str.replace(r"Bewertung(en)?", "", regex=True)
            .str.replace(".", "")
        )
        df = df[df["have"].notna() | df["want"].notna()]
        df["number_of_ratings"] = df.number_of_ratings.astype(int)
        df = df[
            (df.star_rating >= 97.8) & (df.number_of_ratings >= 10)
        ]  # Delete all rows where Star Rating is beneath 98 or number of ratings is under 10
        df["release"] = df.release_page.str.extract(
            r"(\d+)"
        )  # Extract functions requires value in enclosed brackets => Wrong: r"\d+"; Right: r"(\d+)"
        df = df[
            ~df["title"].str.lower().str.contains(r"unofficial")
        ]  # Drop unofficial releases.

        df["media_condition"] = df["media_condition"].str.extract(r"(\(.*\))")
        df["deal_quotient"] = df["media_condition"] == "(M)"
        # Assign value based on condition
        df.loc[df["media_condition"] == "(M)", "media_wert"] = 1
        df.loc[df["media_condition"] == "(NM or M-)", "media_wert"] = 0.8
        df.loc[df["media_condition"] == "(VG+)", "media_wert"] = 0.6
        df.loc[df["media_condition"] == "(VG)", "media_wert"] = 0.4

        df["total_price_in_euro"] = (
            df["total_price_in_euro"]
            .str.replace("€", "")
            .str.replace("insgesamt", "")
            .str.replace("etwa", "")
        )
        # Delete first dot for prices over 1k => e.g. 1.300.50
        df.loc[df["total_price_in_euro"].str.count(r"\.") == 2, "total_price_in_euro"] = df[
            "total_price_in_euro"
        ].str.replace(".", "", 1)
        df["total_price_in_euro"] = df["total_price_in_euro"].astype(float)

        df["deal_quotient"] = (
            df["media_wert"] * (df["want"] / df["have"]) / df["total_price_in_euro"]
        )
        df = df.sort_values("deal_quotient", ascending=False)
        df.to_csv("processed.csv", index=False)

    def get_best_deals(self) -> None:
        """Get top three deals."""
        with open("processed.csv") as f:
            topTen = csv.reader(f, delimiter=",")
            for index, row in enumerate(topTen):
                if index == 0:
                    continue
                if index == 4:
                    break
                webbrowser.open(self.base_url + row[-4])
                time.sleep(1)
        os.remove("raw.csv")
        os.remove("processed.csv")


if __name__ == "__main__":
    release = DiscogsScraper("kill em all")
    release.find_master()
    release.extract()
    release.process_raw_csv()
    release.get_best_deals()
