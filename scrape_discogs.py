#! /Users/marko/Desktop/DiScraper/venv/bin/python3

import requests
import time
import random 
import re
import click

import pandas as pd
from bs4 import BeautifulSoup


HEADERS = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "de-de",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36",
}

BASE_URL = "https://www.discogs.com"


def wait() -> time:
    """Wait 10-20 seconds to slow scraping down."""
    return time.sleep(random.randrange(3, 5))


def read_url_with_headers(url: str):
    """Read URL with hardcoded headers."""
    wait()
    return requests.get(url, headers=HEADERS)


def find_master(album: str, artist: str = "") -> str:
    """Find master release for specified album and artist [optionally]."""
    album = "-".join(album.split())
    album_master_releases_url = f"{BASE_URL}/search/?q={album}&type=master"
    master_releases_tree = BeautifulSoup(
        read_url_with_headers(album_master_releases_url).text, "lxml"
    )
    master_releases = master_releases_tree.find_all(
        "div", attrs={"data-object-type": "master release"}
    )
    m_id_regex = re.compile(r"\d+")
    if not artist:
        click.echo("No Artist specified")
        master_url = master_releases[0].find("a")["href"]
        master_id = m_id_regex.search(master_url).group(0)
    else:
        print("Artist specified")
        for master_release in master_releases:
            master_url = master_release.find("a")["href"]
            if (album in master_url.lower()) and (
                "-".join(artist.split()) in master_url.lower()
            ):
                master_id = m_id_regex.search(master_url).group(0)
                break
    try:
        marketplace_url = f"{BASE_URL}/sell/list?sort=condition%2Cdesc&limit=250&master_id={master_id}&ev=mb"
        return marketplace_url
    except UnboundLocalError:
        album = album.replace("-", " ")
        return f"{album} für {artist} konnte leider nicht gefunden werden."


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

        for release in releases:
            media_condition = release.find(
                "p", attrs={"class": "item_condition"}
            ).find_all("span")[2]
            if (media_condition is None) or (media_condition == "Good Plus (G+)"):
                next_page = False
                continue
            title = release.find("a", class_="item_description_title")
            selling_page = release.find("a", class_="item_description_title")["href"]
            print(selling_page)
            have = release.find(class_=re.compile(r"have_indicator.*?"))
            want = release.find(class_=re.compile(r"want_indicator.*?"))
            try:
                star_rating = release.find("span", class_="star_rating").parent.find(
                    "strong"
                )
            except:
                star_rating = ""
            try:
                number_of_ratings = release.find(
                    "span", attrs={"class": "star_rating"}
                ).find_next_sibling("a")
            except:
                number_of_ratings = ""
            price = release.find("span", attrs={"class": "price"})
            shipping_costs = release.find("span", class_="hide_mobile item_shipping")
            total_price_in_euro = release.find("span", class_="converted_price")
            ships_from = release.find_all("td", attrs={"class": "seller_info"})[
                0
            ].find_all("li")[2]
            sleeve_condition = release.find("p", class_="item_condition").find(
                "span", class_="item_sleeve_condition"
            )
            try:
                individual_text = release.find_all("p", attrs={"class": "hide_mobile"})[
                    1
                ]
            except:
                individual_text = ""
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
                price,
                shipping_costs,
                total_price_in_euro,
                ships_from,
                media_condition,
                sleeve_condition,
                individual_text,
                release_page,
                selling_page
            ]

            keys = [
                "title",
                "have",
                "want",
                "star_rating",
                "number_of_ratings",
                "price",
                "shipping_costs",
                "total_price_in_euro",
                "ships_from",
                "media_condition",
                "sleeve_condition",
                "individual_text",
                "release_page",
                "selling_page"
            ]

            values = []
            # ["href"] -> Beispiel um auf beliebiges Attribut zuzugreifen. job.span.tr.a -> um tags zu traversen.
            for item in raw_data:
                if item is not None:
                    try:
                        values.append(item.text.strip().replace(",", "."))
                    except:
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
    album_cover_src = releases[0].find("td").a.img["data-src"]
    releases_df.to_csv("raw.csv", index=False)
    with open("album.jpeg", "wb") as f:
        f.write(read_url_with_headers(album_cover_src).content)

# def load(df_and_cover: list) -> None:
#     df_and_cover[0].to_csv("releases2.csv", index=False)
#     with open(f"album_cover2.jpeg", "wb") as f:
#         f.write(read_url_with_headers(df_and_cover[1]).content)


if __name__ == "__main__":
    extract(find_master("kill em all"))