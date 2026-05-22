import httpx
import pytest

from scrapi_sdk import ProxyType, ResponseFormat, ScrapeRequest, ScrapiClient, ScrapiException


def _build_client() -> ScrapiClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"requestUrl": "https://deventerprise.com", "Content": "ok"})

    return ScrapiClient("api-key", transport=httpx.MockTransport(handler))


@pytest.mark.parametrize(
    ("mutator", "expected_message"),
    [
        (lambda r: setattr(r, "url", ""), "URL cannot be null/blank."),
        (lambda r: setattr(r, "url", "ftp://deventerprise.com"), "Invalid URL protocol."),
        (
            lambda r: setattr(r, "proxy_country", "US"),
            "Proxy country must be exactly 3 characters long (e.g., 'USA', 'GBR', 'ZAF').",
        ),
        (
            lambda r: setattr(r, "proxy_city", "NewYork"),
            "Proxy country must be specified when proxy city is provided.",
        ),
        (
            lambda r: (
                setattr(r, "proxy_country", "USA"),
                setattr(r, "proxy_type", ProxyType.NONE),
            ),
            "Cannot specify a proxy country when not using a proxy (Residential or DataCenter) or when using Tor.",
        ),
        (
            lambda r: r.browser_commands.click("#go"),
            "Cannot use browser commands unless you are using a browser. Set UseBrowser = true.",
        ),
        (
            lambda r: setattr(r, "solve_captchas", True),
            "Cannot solve captchas unless you are using a browser. Set UseBrowser = true.",
        ),
        (
            lambda r: setattr(r, "include_screenshot", True),
            "Cannot include a screenshot unless you are using a browser. Set UseBrowser = true.",
        ),
        (
            lambda r: setattr(r, "include_pdf", True),
            "Cannot include a PDF unless you are using a browser. Set UseBrowser = true.",
        ),
        (
            lambda r: setattr(r, "include_video", True),
            "Cannot include a video unless you are using a browser. Set UseBrowser = true.",
        ),
        (
            lambda r: setattr(r, "response_format", ResponseFormat.HTML),
            "The client only supports the JSON response format.",
        ),
    ],
)
def test_validation_messages_match_csharp(mutator, expected_message: str) -> None:
    client = _build_client()
    try:
        request = ScrapeRequest("https://deventerprise.com")
        mutator(request)

        with pytest.raises(ScrapiException) as exc_info:
            client.scrape(request)

        assert str(exc_info.value) == expected_message
    finally:
        client.close()


def test_proxy_country_disallowed_for_tor() -> None:
    client = _build_client()
    try:
        request = ScrapeRequest("https://deventerprise.com")
        request.proxy_country = "USA"
        request.proxy_type = ProxyType.TOR

        with pytest.raises(ScrapiException) as exc_info:
            client.scrape(request)

        assert str(exc_info.value) == (
            "Cannot specify a proxy country when not using a proxy (Residential or DataCenter) or when using Tor."
        )
    finally:
        client.close()
