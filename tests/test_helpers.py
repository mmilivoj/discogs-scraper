
from .context import discogs_scraper

def test_read_url_with_headers():
    response = discogs_scraper.helpers.read_url_with_headers("https://www.discogs.com/")
    assert response.status_code == 200
