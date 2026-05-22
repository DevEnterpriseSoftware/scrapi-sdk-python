import json

import httpx
import pytest

from scrapi_sdk import ScrapeRequest, ScrapiClient, ScrapiException


def test_sync_scrape_success_and_wire_payload() -> None:
    seen_payload: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/scrape":
            seen_payload.update(json.loads(request.content.decode("utf-8")))
            return httpx.Response(
                200,
                json={
                    "requestUrl": "https://deventerprise.com",
                    "responseUrl": "https://deventerprise.com/",
                    "duration": "00:00:01.000",
                    "attempts": 1,
                    "captchasSolved": {"hcaptcha": 1},
                    "creditsUsed": 2,
                    "statusCode": 200,
                    "headers": {"content-type": "text/html"},
                    "cookies": {"a": "b"},
                    "content": "<html>Hello</html>",
                },
            )

        raise AssertionError(f"Unexpected path: {request.url.path}")

    client = ScrapiClient("api-key", transport=httpx.MockTransport(handler))
    try:
        response = client.scrape(ScrapeRequest("https://deventerprise.com"))

        assert response is not None
        assert response.request_url == "https://deventerprise.com"
        assert response.credits_used == 2
        assert seen_payload["responseFormat"] == "Json"
        assert seen_payload["url"] == "https://deventerprise.com"
    finally:
        client.close()


def test_sync_404_returns_none_empty_and_zero() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    client = ScrapiClient("api-key", transport=httpx.MockTransport(handler))
    try:
        assert client.scrape("https://deventerprise.com") is None
        assert client.get_supported_countries() == []
        assert client.get_supported_cities("USA") == []
        assert client.get_credit_balance() == 0
    finally:
        client.close()


def test_sync_invalid_json_maps_to_scrapi_exception() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not-json", headers={"Content-Type": "application/json"})

    client = ScrapiClient("api-key", transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ScrapiException) as exc_info:
            client.scrape("https://deventerprise.com")

        assert str(exc_info.value) == "Invalid JSON response."
    finally:
        client.close()


def test_sync_timeout_maps_to_408() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Timed out", request=request)

    client = ScrapiClient("api-key", transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ScrapiException) as exc_info:
            client.scrape("https://deventerprise.com")

        assert exc_info.value.status_code == 408
    finally:
        client.close()


def test_sync_http_error_maps_status_code() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"message": "boom"}, request=request)

    client = ScrapiClient("api-key", transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ScrapiException) as exc_info:
            client.scrape("https://deventerprise.com")

        assert exc_info.value.status_code == 500
    finally:
        client.close()
