"""CLI-App."""
import click

from scrape_discogs import find_master, extract
from analysis import process_raw_csv, get_top_ten_deals

@click.command()
@click.option("--album", default="", help='Provide the title of the LP to be searched on "https://www.discogs.com".')
@click.option("--artist", default="", help="Specify the artist or band of your desired LP.")
def scrape(album: str, artist: str = "") -> None:
    """Scrape the top ten deals for a given album (and artist/band optionally)."""
    if not album:
        click.secho("Please specify an album title.", fg="yellow")
        return
    click.secho("Connecting to Discogs...", fg="green")
    master = find_master(album, artist)
    click.secho("Scraping information from Discogs...", fg="green")
    extract(master)
    click.secho("Filtering deals.", fg="green")
    process_raw_csv()
    click.secho("Top Ten Deals:", fg="green")
    get_top_ten_deals()


if __name__ == "__main__":
    scrape()

# TODO: Der zieht Kassetten... WTF. musss den Link anpassen