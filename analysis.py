"""Analyzing the scraped information to find the best deals."""

import csv

import pandas as pd
import warnings
warnings.filterwarnings('ignore')


def process_raw_csv() -> None:
    df = pd.read_csv("raw.csv")
    df['star_rating'] = df['star_rating'].str.replace('%', '').astype('float')
    df['ships_from'] = df['ships_from'].str.replace('Versand aus:', '').str.strip()
    df = df[df["number_of_ratings"].notna()]
    df['number_of_ratings'] = df['number_of_ratings'].str.replace(r'Bewertung(en)?', '', regex=True).str.replace(".", "")
    df = df[df["have"].notna() | df["want"].notna()]
    df["number_of_ratings"] = df.number_of_ratings.astype(int)
    df = df[(df.star_rating > 98.0) & (df.number_of_ratings >= 10)]  # Delete all rows where Star Rating is beneath 98 or number of ratings is under 10
    df["release"] = df.release_page.str.extract(r"(\d+)")  # Extract functions requires value in enclosed brackets => Wrong: r"\d+"; Right: r"(\d+)"
    df = df[~df["title"].str.lower().str.contains(r"unofficial")]  # Drop unofficial releases.
    df["wanted_ratio"] = df["want"] / df["have"]


    df["media_condition"] = df["media_condition"].str.extract(r"(\(.*\))")
    df["sleeve_condition"] = df["sleeve_condition"].str.extract(r"(\(.*\))")
    df["deal_quotient"] = df["media_condition"] == "(M)" 
    df.loc[df["media_condition"] == "(M)", "media_wert"] = 1
    df.loc[df["media_condition"] == "(NM or M-)", "media_wert"] = 0.8
    df.loc[df["media_condition"] == "(VG+)", "media_wert"] = 0.6
    df.loc[df["media_condition"] == "(VG)", "media_wert"] = 0.4

    df["total_price_in_euro"] = df["total_price_in_euro"].str.replace("€", "").str.replace("insgesamt", "").str.replace("etwa", "")
    df.loc[df["total_price_in_euro"].str.count(r"\.") == 2, "total_price_in_euro"] = df["total_price_in_euro"].str.replace(".", "", 1)
    df["total_price_in_euro"] = df["total_price_in_euro"].astype(float)

    df["deal_quotient"] = df["media_wert"] * (df["want"] / df["have"]) / df["total_price_in_euro"]
    df = df.sort_values("deal_quotient", ascending=False)
    df.to_csv("processed.csv", index=False)
    


def get_top_ten_deals() -> None:
    with open("processed.csv") as f:
        topTen = csv.reader(f, delimiter=",")
        for index, row in enumerate(topTen):
            if index == 0:
                continue
            if index == 11:
                break
            print(f"Top {index}: https://www.discogs.com{row[-5]}")


