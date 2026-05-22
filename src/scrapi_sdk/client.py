from __future__ import annotations

import json
from typing import Any, Mapping

import httpx

from .enums import ProxyType, ResponseFormat
from .exceptions import ScrapiException
from .models import (
    BalanceResponse,
    ScrapeRequest,
    ScrapeResponse,
    SupportedCityResponse,
    SupportedCountryResponse,
)
from .version import __version__

API_URL = "https://api.scrapi.tech"
API_HEALTH_URL = "https://api.scrapi.tech/health"
_DEFAULT_TIMEOUT_SECONDS = 300.0


def _has_text(value: str | None) -> bool:
    return value is not None and value.strip() != ""


def _make_default_headers(api_key: str) -> dict[str, str]:
    return {
        "Accept": "application/json",
        "User-Agent": f"ScrAPI Python SDK - {__version__}",
        "X-API-KEY": api_key,
    }


def _validate_scrape_request(request: ScrapeRequest | None) -> ScrapeRequest:
    if request is None:
        raise ValueError("request")

    request_url = (request.url or "").strip()

    if request_url == "":
        raise ScrapiException(message="URL cannot be null/blank.")

    if not request_url.lower().startswith("http"):
        raise ScrapiException(message="Invalid URL protocol.")

    if _has_text(request.proxy_country) and len(request.proxy_country or "") != 3:
        raise ScrapiException(
            message="Proxy country must be exactly 3 characters long (e.g., 'USA', 'GBR', 'ZAF')."
        )

    if _has_text(request.proxy_city) and not _has_text(request.proxy_country):
        raise ScrapiException(message="Proxy country must be specified when proxy city is provided.")

    if _has_text(request.proxy_country) and request.proxy_type in (ProxyType.NONE, ProxyType.TOR):
        raise ScrapiException(
            message=(
                "Cannot specify a proxy country when not using a proxy "
                "(Residential or DataCenter) or when using Tor."
            )
        )

    if len(request.browser_commands) > 0 and not request.use_browser:
        raise ScrapiException(
            message=(
                "Cannot use browser commands unless you are using a browser. "
                "Set UseBrowser = true."
            )
        )

    if request.solve_captchas and not request.use_browser:
        raise ScrapiException(
            message=(
                "Cannot solve captchas unless you are using a browser. "
                "Set UseBrowser = true."
            )
        )

    if request.include_screenshot and not request.use_browser:
        raise ScrapiException(
            message=(
                "Cannot include a screenshot unless you are using a browser. "
                "Set UseBrowser = true."
            )
        )

    if request.include_pdf and not request.use_browser:
        raise ScrapiException(
            message=(
                "Cannot include a PDF unless you are using a browser. "
                "Set UseBrowser = true."
            )
        )

    if request.include_video and not request.use_browser:
        raise ScrapiException(
            message=(
                "Cannot include a video unless you are using a browser. "
                "Set UseBrowser = true."
            )
        )

    if request.response_format != ResponseFormat.JSON:
        raise ScrapiException(message="The client only supports the JSON response format.")

    return request


class ScrapiClient:
    def __init__(
        self,
        api_key: str,
        *,
        timeout: float = _DEFAULT_TIMEOUT_SECONDS,
        base_url: str = API_URL,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._http_client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers=_make_default_headers(api_key),
            transport=transport,
        )

    def close(self) -> None:
        self._http_client.close()

    def __enter__(self) -> ScrapiClient:
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.close()

    def scrape(self, request_or_url: ScrapeRequest | str) -> ScrapeResponse | None:
        request = request_or_url if isinstance(request_or_url, ScrapeRequest) else ScrapeRequest(request_or_url)
        _validate_scrape_request(request)

        data = self._make_api_call("POST", "v1/scrape", request.to_api_dict())
        if data is None:
            return None

        return ScrapeResponse.from_api_dict(data)

    def get_supported_countries(self) -> list[SupportedCountryResponse]:
        data = self._make_api_call("GET", "v1/countries")
        if data is None:
            return []

        return [SupportedCountryResponse.from_api_dict(item) for item in data]

    def get_supported_cities(self, country_key: str) -> list[SupportedCityResponse]:
        data = self._make_api_call("GET", f"v1/countries/{country_key}/cities")
        if data is None:
            return []

        return [SupportedCityResponse.from_api_dict(item) for item in data]

    def get_credit_balance(self) -> int:
        data = self._make_api_call("GET", "v1/balance")
        if data is None:
            return 0

        return BalanceResponse.from_api_dict(data).credits

    def _make_api_call(self, method: str, url: str, data: Mapping[str, Any] | None = None) -> Any:
        response: httpx.Response | None = None

        try:
            response = self._http_client.request(method, url, json=data)

            if response.status_code == 404:
                return None

            response.raise_for_status()

            if response.content is None or len(response.content) == 0:
                return None

            try:
                return response.json()
            except (ValueError, json.JSONDecodeError) as ex:
                raise ScrapiException(
                    status_code=response.status_code,
                    message="Invalid JSON response.",
                    inner_exception=ex,
                ) from ex

        except ScrapiException:
            raise
        except httpx.TimeoutException as ex:
            raise ScrapiException(status_code=408, message=str(ex), inner_exception=ex) from ex
        except httpx.HTTPStatusError as ex:
            raise ScrapiException(
                status_code=ex.response.status_code,
                message=str(ex),
                inner_exception=ex,
            ) from ex
        except httpx.RequestError as ex:
            code = response.status_code if response is not None else None
            raise ScrapiException(status_code=code, message=str(ex), inner_exception=ex) from ex


class AsyncScrapiClient:
    def __init__(
        self,
        api_key: str,
        *,
        timeout: float = _DEFAULT_TIMEOUT_SECONDS,
        base_url: str = API_URL,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._http_client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers=_make_default_headers(api_key),
            transport=transport,
        )

    async def close(self) -> None:
        await self._http_client.aclose()

    async def __aenter__(self) -> AsyncScrapiClient:
        return self

    async def __aexit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        await self.close()

    async def scrape(self, request_or_url: ScrapeRequest | str) -> ScrapeResponse | None:
        request = request_or_url if isinstance(request_or_url, ScrapeRequest) else ScrapeRequest(request_or_url)
        _validate_scrape_request(request)

        data = await self._make_api_call("POST", "v1/scrape", request.to_api_dict())
        if data is None:
            return None

        return ScrapeResponse.from_api_dict(data)

    async def get_supported_countries(self) -> list[SupportedCountryResponse]:
        data = await self._make_api_call("GET", "v1/countries")
        if data is None:
            return []

        return [SupportedCountryResponse.from_api_dict(item) for item in data]

    async def get_supported_cities(self, country_key: str) -> list[SupportedCityResponse]:
        data = await self._make_api_call("GET", f"v1/countries/{country_key}/cities")
        if data is None:
            return []

        return [SupportedCityResponse.from_api_dict(item) for item in data]

    async def get_credit_balance(self) -> int:
        data = await self._make_api_call("GET", "v1/balance")
        if data is None:
            return 0

        return BalanceResponse.from_api_dict(data).credits

    async def _make_api_call(self, method: str, url: str, data: Mapping[str, Any] | None = None) -> Any:
        response: httpx.Response | None = None

        try:
            response = await self._http_client.request(method, url, json=data)

            if response.status_code == 404:
                return None

            response.raise_for_status()

            if response.content is None or len(response.content) == 0:
                return None

            try:
                return response.json()
            except (ValueError, json.JSONDecodeError) as ex:
                raise ScrapiException(
                    status_code=response.status_code,
                    message="Invalid JSON response.",
                    inner_exception=ex,
                ) from ex

        except ScrapiException:
            raise
        except httpx.TimeoutException as ex:
            raise ScrapiException(status_code=408, message=str(ex), inner_exception=ex) from ex
        except httpx.HTTPStatusError as ex:
            raise ScrapiException(
                status_code=ex.response.status_code,
                message=str(ex),
                inner_exception=ex,
            ) from ex
        except httpx.RequestError as ex:
            code = response.status_code if response is not None else None
            raise ScrapiException(status_code=code, message=str(ex), inner_exception=ex) from ex
