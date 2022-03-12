"""Scraping and analyzing functions for core module."""

import requests
import time
import random
import re
import csv
import os
import webbrowser
import click

from requests.exceptions import ConnectionError
import pandas as pd
from bs4 import BeautifulSoup
import warnings

warnings.filterwarnings('ignore')

# Specify real-world headers, as otherwise the "requests"-library uses headers that indicate a scraping machine.
HEADERS = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "de-de",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36",  # noqa: E501
}

BASE_URL = "https://www.discogs.com"


def wait() -> time:
    """Wait 2-4 seconds to slow scraping down."""
    return time.sleep(random.randrange(2, 4))


def read_url_with_headers(url: str):
    """Read URL with hardcoded headers."""
    wait()
    return requests.get(url, headers=HEADERS)


def find_master(album: str, artist: str = "") -> str:
    """Find master release for specified album and artist [optionally]."""
    if not album:
        click.secho("Please specify an album title.", fg="yellow")

    album = "-".join(album.split())
    album_master_releases_url = f"{BASE_URL}/search/?q={album}&type=master"
    try:
        master_releases_tree = BeautifulSoup(
            read_url_with_headers(album_master_releases_url).text, "lxml"
        )
    except ConnectionError:
        raise SystemExit
    master_releases = master_releases_tree.find_all(
        "div", attrs={"data-object-type": "master release"}
    )
    m_id_regex = re.compile(r"\d+")  # search schema for id of master release
    if not artist:
        # No Artist specified
        master_url = master_releases[0].find("a")["href"]
        master_id = m_id_regex.search(master_url).group(0)
    else:
        # Artist specified
        for master_release in master_releases:
            master_url = master_release.find("a")["href"]
            if (album.lower() in master_url.lower()) and (
                "-".join(artist.split()).lower() in master_url.lower()
            ):
                master_id = m_id_regex.search(master_url).group(0)
                break
    try:
        marketplace_url = f"{BASE_URL}/sell/list?sort=condition%2Cdesc&limit=250&master_id={master_id}&ev=mb&format=Vinyl"
        return marketplace_url
    except UnboundLocalError:
        # UnboundLocalError thrown, if master_id was not assigned a value.
        # Happens when a combination of artist and album is specified, that is not available on Discogs.com
        album = album.replace("-", " ")
        print(f"{album} by {artist} could not be identified.")
        raise SystemExit


def extract(marketplace_url: str) -> None:
    """Extract all releases from marketplace."""
    data_set = []
    page_nr = 1
    next_page = True
    while next_page:
        url = marketplace_url + f"&page={page_nr}"
        html_doc = read_url_with_headers(url).text
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
                BASE_URL
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


def get_best_deals() -> None:
    """Get top three deals."""
    with open("processed.csv") as f:
        topTen = csv.reader(f, delimiter=",")
        for index, row in enumerate(topTen):
            if index == 0:
                continue
            if index == 4:
                break
            webbrowser.open(BASE_URL + row[-4])
            wait()
    os.remove("raw.csv")
    os.remove("processed.csv")  # x
