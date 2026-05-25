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
"""The base URL for the ScrAPI service."""

API_HEALTH_URL = "https://api.scrapi.tech/health"
"""The health check URL for the ScrAPI service."""
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
    """The official ScrAPI client for synchronous web scraping operations.

    Provides synchronous methods to interact with the ScrAPI service,
    including scraping URLs, retrieving supported proxy locations, and
    checking credit balances.

    This client can be used as a context manager to ensure the underlying
    HTTP connection is properly closed::

        with ScrapiClient("your-api-key") as client:
            response = client.scrape("https://example.com")

    Args:
        api_key: The API key issued when registering at https://scrapi.tech.
        timeout: The request timeout in seconds. Defaults to 300.
        base_url: The base URL for the ScrAPI API. Defaults to :data:`API_URL`.
        transport: An optional custom HTTP transport for the underlying
            ``httpx`` client.
    """

    def __init__(
        self,
        api_key: str,
        *,
        timeout: float = _DEFAULT_TIMEOUT_SECONDS,
        base_url: str = API_URL,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """Initialize a new :class:`ScrapiClient`.

        Args:
            api_key: The API key issued when registering at https://scrapi.tech.
            timeout: The request timeout in seconds. Defaults to 300.
            base_url: The base URL for the ScrAPI API. Defaults to :data:`API_URL`.
            transport: An optional custom HTTP transport for the underlying
                ``httpx`` client.
        """
        self._http_client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers=_make_default_headers(api_key),
            transport=transport,
        )

    def close(self) -> None:
        """Close the underlying HTTP client and release all resources.

        Called automatically when used as a context manager.
        """
        self._http_client.close()

    def __enter__(self) -> ScrapiClient:
        """Enter the runtime context and return this client.

        Returns:
            This :class:`ScrapiClient` instance.
        """
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        """Exit the runtime context and close the HTTP client."""
        self.close()

    def scrape(self, request_or_url: ScrapeRequest | str) -> ScrapeResponse | None:
        """Perform a web scraping operation on the provided URL.

        Args:
            request_or_url: Either a :class:`~scrapi_sdk.models.ScrapeRequest`
                with full options, or a plain URL string to scrape with defaults.

        Returns:
            A :class:`~scrapi_sdk.models.ScrapeResponse` containing the scraped
            content, or ``None`` if the resource was not found.

        Raises:
            ValueError: If ``request_or_url`` is ``None``.
            ScrapiException: If there are problems with the scrape operation.
        """
        request = request_or_url if isinstance(request_or_url, ScrapeRequest) else ScrapeRequest(request_or_url)
        _validate_scrape_request(request)

        data = self._make_api_call("POST", "v1/scrape", request.to_api_dict())
        if data is None:
            return None

        return ScrapeResponse.from_api_dict(data)

    def get_supported_countries(self) -> list[SupportedCountryResponse]:
        """Get a list of countries supported for proxy geolocation.

        The list typically updates every 30 minutes. Country keys returned
        here can be used as the
        :attr:`~scrapi_sdk.models.ScrapeRequest.proxy_country` value.

        Returns:
            A list of :class:`~scrapi_sdk.models.SupportedCountryResponse`
            objects, or an empty list if none are available.

        Raises:
            ScrapiException: If there are problems fetching the country list.
        """
        data = self._make_api_call("GET", "v1/countries")
        if data is None:
            return []

        return [SupportedCountryResponse.from_api_dict(item) for item in data]

    def get_supported_cities(self, country_key: str) -> list[SupportedCityResponse]:
        """Get a list of cities supported for proxy geolocation within a country.

        The list typically updates every 30 minutes. City keys returned here
        can be used as the
        :attr:`~scrapi_sdk.models.ScrapeRequest.proxy_city` value.

        Args:
            country_key: The three-letter country code (e.g. ``"USA"``,
                ``"GBR"``) to retrieve cities for.

        Returns:
            A list of :class:`~scrapi_sdk.models.SupportedCityResponse`
            objects, or an empty list if none are available.

        Raises:
            ScrapiException: If there are problems fetching the city list.
        """
        data = self._make_api_call("GET", f"v1/countries/{country_key}/cities")
        if data is None:
            return []

        return [SupportedCityResponse.from_api_dict(item) for item in data]

    def get_credit_balance(self) -> int:
        """Get the current credit balance for your API key.

        The balance may be negative when concurrent requests complete
        simultaneously.

        Returns:
            The current credit balance as an integer.

        Raises:
            ScrapiException: If there are problems fetching the balance.
        """
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
    """The official ScrAPI client for asynchronous web scraping operations.

    Provides asynchronous methods to interact with the ScrAPI service,
    including scraping URLs, retrieving supported proxy locations, and
    checking credit balances.

    This client can be used as an async context manager to ensure the
    underlying HTTP connection is properly closed::

        async with AsyncScrapiClient("your-api-key") as client:
            response = await client.scrape("https://example.com")

    Args:
        api_key: The API key issued when registering at https://scrapi.tech.
        timeout: The request timeout in seconds. Defaults to 300.
        base_url: The base URL for the ScrAPI API. Defaults to :data:`API_URL`.
        transport: An optional custom async HTTP transport for the underlying
            ``httpx`` client.
    """

    def __init__(
        self,
        api_key: str,
        *,
        timeout: float = _DEFAULT_TIMEOUT_SECONDS,
        base_url: str = API_URL,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        """Initialize a new :class:`AsyncScrapiClient`.

        Args:
            api_key: The API key issued when registering at https://scrapi.tech.
            timeout: The request timeout in seconds. Defaults to 300.
            base_url: The base URL for the ScrAPI API. Defaults to :data:`API_URL`.
            transport: An optional custom async HTTP transport for the underlying
                ``httpx`` client.
        """
        self._http_client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers=_make_default_headers(api_key),
            transport=transport,
        )

    async def close(self) -> None:
        """Close the underlying async HTTP client and release all resources.

        Called automatically when used as an async context manager.
        """
        await self._http_client.aclose()

    async def __aenter__(self) -> AsyncScrapiClient:
        """Enter the async runtime context and return this client.

        Returns:
            This :class:`AsyncScrapiClient` instance.
        """
        return self

    async def __aexit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        """Exit the async runtime context and close the HTTP client."""
        await self.close()

    async def scrape(self, request_or_url: ScrapeRequest | str) -> ScrapeResponse | None:
        """Perform an asynchronous web scraping operation on the provided URL.

        Args:
            request_or_url: Either a :class:`~scrapi_sdk.models.ScrapeRequest`
                with full options, or a plain URL string to scrape with defaults.

        Returns:
            A :class:`~scrapi_sdk.models.ScrapeResponse` containing the scraped
            content, or ``None`` if the resource was not found.

        Raises:
            ValueError: If ``request_or_url`` is ``None``.
            ScrapiException: If there are problems with the scrape operation.
        """
        request = request_or_url if isinstance(request_or_url, ScrapeRequest) else ScrapeRequest(request_or_url)
        _validate_scrape_request(request)

        data = await self._make_api_call("POST", "v1/scrape", request.to_api_dict())
        if data is None:
            return None

        return ScrapeResponse.from_api_dict(data)

    async def get_supported_countries(self) -> list[SupportedCountryResponse]:
        """Get a list of countries supported for proxy geolocation.

        The list typically updates every 30 minutes. Country keys returned
        here can be used as the
        :attr:`~scrapi_sdk.models.ScrapeRequest.proxy_country` value.

        Returns:
            A list of :class:`~scrapi_sdk.models.SupportedCountryResponse`
            objects, or an empty list if none are available.

        Raises:
            ScrapiException: If there are problems fetching the country list.
        """
        data = await self._make_api_call("GET", "v1/countries")
        if data is None:
            return []

        return [SupportedCountryResponse.from_api_dict(item) for item in data]

    async def get_supported_cities(self, country_key: str) -> list[SupportedCityResponse]:
        """Get a list of cities supported for proxy geolocation within a country.

        The list typically updates every 30 minutes. City keys returned here
        can be used as the
        :attr:`~scrapi_sdk.models.ScrapeRequest.proxy_city` value.

        Args:
            country_key: The three-letter country code (e.g. ``"USA"``,
                ``"GBR"``) to retrieve cities for.

        Returns:
            A list of :class:`~scrapi_sdk.models.SupportedCityResponse`
            objects, or an empty list if none are available.

        Raises:
            ScrapiException: If there are problems fetching the city list.
        """
        data = await self._make_api_call("GET", f"v1/countries/{country_key}/cities")
        if data is None:
            return []

        return [SupportedCityResponse.from_api_dict(item) for item in data]

    async def get_credit_balance(self) -> int:
        """Get the current credit balance for your API key.

        The balance may be negative when concurrent requests complete
        simultaneously.

        Returns:
            The current credit balance as an integer.

        Raises:
            ScrapiException: If there are problems fetching the balance.
        """
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
