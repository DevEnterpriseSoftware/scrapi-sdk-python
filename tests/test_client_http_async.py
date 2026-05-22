import httpx
import pytest

from scrapi_sdk import AsyncScrapiClient, ScrapiException


@pytest.mark.asyncio
async def test_async_scrape_success() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "requestUrl": "https://deventerprise.com",
                "responseUrl": "https://deventerprise.com/",
                "duration": "00:00:01.000",
                "attempts": 1,
                "creditsUsed": 1,
                "statusCode": 200,
                "headers": {},
                "cookies": {},
                "content": "<html>ok</html>",
            },
            request=request,
        )

    client = AsyncScrapiClient("api-key", transport=httpx.MockTransport(handler))
    try:
        response = await client.scrape("https://deventerprise.com")
        assert response is not None
        assert response.request_url == "https://deventerprise.com"
        assert response.credits_used == 1
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_async_404_fallbacks() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, request=request)

    client = AsyncScrapiClient("api-key", transport=httpx.MockTransport(handler))
    try:
        assert await client.scrape("https://deventerprise.com") is None
        assert await client.get_supported_countries() == []
        assert await client.get_supported_cities("USA") == []
        assert await client.get_credit_balance() == 0
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_async_invalid_json_and_timeout_mappings() -> None:
    async def invalid_json_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="nope", request=request)

    client = AsyncScrapiClient("api-key", transport=httpx.MockTransport(invalid_json_handler))
    try:
        with pytest.raises(ScrapiException, match="Invalid JSON response"):
            await client.scrape("https://deventerprise.com")
    finally:
        await client.close()

    async def timeout_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Timeout", request=request)

    client2 = AsyncScrapiClient("api-key", transport=httpx.MockTransport(timeout_handler))
    try:
        with pytest.raises(ScrapiException) as exc_info:
            await client2.scrape("https://deventerprise.com")
        assert exc_info.value.status_code == 408
    finally:
        await client2.close()
