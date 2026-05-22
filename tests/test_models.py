import hashlib

from scrapi_sdk.defaults import ScrapeRequestDefaults
from scrapi_sdk.models import ScrapeRequest, ScrapeResponse


def test_scrape_request_copies_mutable_defaults() -> None:
    old_cookies = ScrapeRequestDefaults.cookies
    old_headers = ScrapeRequestDefaults.headers

    try:
        ScrapeRequestDefaults.cookies = {"cookie1": "value1"}
        ScrapeRequestDefaults.headers = {"header1": "value1"}

        request = ScrapeRequest("https://deventerprise.com")

        assert request.cookies == {"cookie1": "value1"}
        assert request.headers == {"header1": "value1"}

        request.cookies["cookie2"] = "value2"
        request.headers["header2"] = "value2"

        assert ScrapeRequestDefaults.cookies == {"cookie1": "value1"}
        assert ScrapeRequestDefaults.headers == {"header1": "value1"}
    finally:
        ScrapeRequestDefaults.cookies = old_cookies
        ScrapeRequestDefaults.headers = old_headers


def test_scrape_request_normalizes_relative_url() -> None:
    request = ScrapeRequest("deventerprise.com")
    assert request.url == "https://deventerprise.com"


def test_scrape_response_content_hash_matches_utf16le_sha1() -> None:
    response = ScrapeResponse(request_url="https://deventerprise.com", content="Hello")

    expected = hashlib.sha1("Hello".encode("utf-16le"), usedforsecurity=False).hexdigest().upper()

    assert response.content_hash == expected


def test_scrape_response_html_property_is_lazy() -> None:
    response = ScrapeResponse(request_url="https://deventerprise.com", content="<html><body><p>A &amp; B</p></body></html>")

    soup = response.html
    assert soup.find("p").get_text() == "A & B"
