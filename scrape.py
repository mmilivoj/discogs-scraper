"""CLI-App."""

import click
from discogs_scraper.core import DiscogsScraper


@click.command()
@click.option(
    "--album",
    default="",
    help='Provide the title of the LP to be searched on "https://www.discogs.com".',
)
@click.option(
    "--by", default="", help="Specify the artist or band of your desired LP."
)
def scrape(album: str, by: str = "") -> None:
    """Scrape the top ten deals for a given album (and artist/band optionally)."""
    release = DiscogsScraper(album, by)

    click.secho("Connecting to Discogs...", fg="green")
    release.find_master()

    click.secho("Scraping information from Discogs...", fg="green")
    release.extract()

    click.secho("Filtering deals...", fg="green")
    release.process_raw_csv()

    click.secho("Opening top three deals...", fg="green")
    release.get_best_deals()


if __name__ == "__main__":
    scrape()