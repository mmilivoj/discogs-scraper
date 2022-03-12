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
    "--artist", default="", help="Specify the artist or band of your desired LP."
)
def scrape(album: str, artist: str = "") -> None:
    """Scrape the top ten deals for a given album (and artist/band optionally)."""
    # if not album:
    #     click.secho("Please specify an album title.", fg="yellow")
    #     return
    click.secho("Connecting to Discogs...", fg="green")
    try:
        master = find_master(album, artist)
    except SystemExit:
        click.secho("Please check your internet connection.", fg="yellow")
        return 
    click.secho("Scraping information from Discogs...", fg="green")
    extraction = extract(master)
    if extraction == "No items for sale.":
        click.secho("No Deals available.", fg="yellow")
        return
    click.secho("Filtering deals...", fg="green")
    process_raw_csv()
    click.secho("Opening top three deals...", fg="green")
    get_best_deals()