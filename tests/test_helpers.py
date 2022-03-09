
from .context import discogs_scraper

def test_read_url_with_headers():
    response = discogs_scraper.helpers.read_url_with_headers("https://www.discogs.com/")
    assert response.status_code == 200
    assert response.request.headers["accept"] == "*/*"
    assert response.request.headers["accept-encoding"] == "gzip, deflate, br"
    assert response.request.headers["accept-language"] == "de-de"
    assert response.request.headers["sec-fetch-dest"] == "empty"
    assert response.request.headers["sec-fetch-mode"] == "cors"
    assert response.request.headers["sec-fetch-site"] == "cross-site"
    assert response.request.headers["user-agent"] == "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36"