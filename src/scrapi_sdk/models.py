from __future__ import annotations

import hashlib
import html
from dataclasses import dataclass, field
from typing import Any, Mapping
from urllib.parse import urlparse

from .browser_commands import BrowserCommandList, commands_from_wire
from .defaults import ScrapeRequestDefaults
from .enums import (
    ProxyType,
    ResponseFormat,
    proxy_type_from_wire,
    proxy_type_to_wire,
    response_format_from_wire,
    response_format_to_wire,
)


def normalize_url(value: str) -> str:
    candidate = (value or "").strip()
    if not candidate:
        return ""

    parsed = urlparse(candidate)
    if parsed.scheme and parsed.netloc:
        return candidate

    upgraded = f"https://{candidate.lstrip(':/')}"
    upgraded_parsed = urlparse(upgraded)
    if upgraded_parsed.scheme and upgraded_parsed.netloc:
        return upgraded

    raise ValueError("The URL provided is not a valid absolute URL.")


@dataclass(slots=True)
class ScrapeRequest:
    """A web scrape request.

    Attributes:
        url: The URL to scrape for content. Must be an absolute URL. If a
            scheme is omitted, ``https://`` is prepended automatically.
        response_format: The response format from the API call. Defaults to
            :attr:`~scrapi_sdk.enums.ResponseFormat.JSON`. Only JSON is
            supported by the client.
        response_selector: A CSS or XPath selector used to filter the response
            content to a specific element. Defaults to ``None``.
        cookies: Key/value pairs of cookies to include in the scrape request.
            Defaults to an empty dictionary.
        headers: Key/value pairs of headers to include in the scrape request.
            ScrAPI will generate certain headers automatically (such as a
            random User-Agent). Headers provided here override those defaults.
            Defaults to an empty dictionary.
        request_method: The HTTP request method to use when requesting the
            target URL. Cannot be used when ``use_browser`` is ``True``.
            Defaults to ``"GET"``.
        request_body_base64: Base64-encoded binary data to send to the target
            website. Requires the ``Content-Type`` header to be set. Cannot
            be used when ``use_browser`` is ``True``. Defaults to ``None``.
        proxy_type: The type of proxy to use for the scrape request. Defaults
            to :attr:`~scrapi_sdk.enums.ProxyType.NONE`.
        proxy_country: The three-letter country code (e.g. ``"USA"``, ``"GBR"``,
            ``"ZAF"``) for geolocation. Use
            :meth:`~scrapi_sdk.client.ScrapiClient.get_supported_countries`
            to retrieve valid codes. Defaults to ``None``.
        proxy_city: The city name for geolocation. Requires ``proxy_country``
            to also be set. Use
            :meth:`~scrapi_sdk.client.ScrapiClient.get_supported_cities`
            to retrieve valid city names. Defaults to ``None``.
        custom_proxy_url: A custom proxy URL in the format
            ``protocol://username:password@host:port``. Username and password
            are optional for unauthenticated proxies. Defaults to ``None``.
        use_browser: Whether to use a full headless browser (executes
            JavaScript) rather than a plain HTTP client call (faster, no
            JavaScript). Defaults to ``False``.
        solve_captchas: Whether to automatically detect, solve, and submit
            captchas. Requires ``use_browser`` to be ``True``. Defaults to
            ``False``.
        include_screenshot: Whether to capture a screenshot of the page and
            include a link in the response. Requires ``use_browser`` to be
            ``True``. Defaults to ``False``.
        include_pdf: Whether to generate a PDF of the page and include a link
            in the response. Requires ``use_browser`` to be ``True``. Defaults
            to ``False``.
        include_video: Whether to record a video of the page and browser
            commands and include a link in the response. Requires
            ``use_browser`` to be ``True``. Defaults to ``False``.
        accept_dialogs: Whether to accept rather than cancel popup dialogs
            when using browser commands. By default all popups are cancelled.
            Defaults to ``False``.
        session_id: An optional session identifier that causes the same IP
            address, user agent, and cookies to be reused across requests
            sharing the same value. Useful to avoid re-solving captchas.
            Defaults to ``None``.
        callback_url: A URL that will receive an HTTP POST with the
            :class:`ScrapeResponse` serialized as JSON when the scraping
            operation completes. Defaults to ``None``.
        browser_commands: An ordered list of browser commands to execute
            after the page has loaded. Requires ``use_browser`` to be
            ``True``. Defaults to an empty :class:`~scrapi_sdk.browser_commands.BrowserCommandList`.
    """

    url: str
    response_format: ResponseFormat = field(default_factory=lambda: ScrapeRequestDefaults.response_format)
    response_selector: str | None = field(default_factory=lambda: ScrapeRequestDefaults.response_selector)
    cookies: dict[str, str] = field(default_factory=lambda: dict(ScrapeRequestDefaults.cookies))
    headers: dict[str, str] = field(default_factory=lambda: dict(ScrapeRequestDefaults.headers))
    request_method: str = field(default_factory=lambda: ScrapeRequestDefaults.request_method)
    request_body_base64: str | None = None
    proxy_type: ProxyType = field(default_factory=lambda: ScrapeRequestDefaults.proxy_type)
    proxy_country: str | None = field(default_factory=lambda: ScrapeRequestDefaults.proxy_country)
    proxy_city: str | None = field(default_factory=lambda: ScrapeRequestDefaults.proxy_city)
    custom_proxy_url: str | None = field(default_factory=lambda: ScrapeRequestDefaults.custom_proxy_url)
    use_browser: bool = field(default_factory=lambda: ScrapeRequestDefaults.use_browser)
    solve_captchas: bool = field(default_factory=lambda: ScrapeRequestDefaults.solve_captchas)
    include_screenshot: bool = field(default_factory=lambda: ScrapeRequestDefaults.include_screenshot)
    include_pdf: bool = field(default_factory=lambda: ScrapeRequestDefaults.include_pdf)
    include_video: bool = field(default_factory=lambda: ScrapeRequestDefaults.include_video)
    accept_dialogs: bool = field(default_factory=lambda: ScrapeRequestDefaults.accept_dialogs)
    session_id: str | None = field(default_factory=lambda: ScrapeRequestDefaults.session_id)
    callback_url: str | None = field(default_factory=lambda: ScrapeRequestDefaults.callback_url)
    browser_commands: BrowserCommandList = field(default_factory=BrowserCommandList)

    def __post_init__(self) -> None:
        """Normalize the URL after initialization."""
        try:
            self.url = normalize_url(self.url)
        except ValueError:
            # Keep invalid values untouched so client validation can return parity messages.
            pass

    def to_api_dict(self) -> dict[str, Any]:
        """Serialize this request to a dictionary suitable for the ScrAPI API.

        Returns:
            A dictionary containing all request fields mapped to their API
            wire names.
        """
        return {
            "url": self.url,
            "responseFormat": response_format_to_wire(self.response_format),
            "responseSelector": self.response_selector,
            "cookies": self.cookies,
            "headers": self.headers,
            "requestMethod": self.request_method,
            "requestBodyBase64": self.request_body_base64,
            "proxyType": proxy_type_to_wire(self.proxy_type),
            "proxyCountry": self.proxy_country,
            "proxyCity": self.proxy_city,
            "customProxyUrl": self.custom_proxy_url,
            "useBrowser": self.use_browser,
            "solveCaptchas": self.solve_captchas,
            "includeScreenshot": self.include_screenshot,
            "includePdf": self.include_pdf,
            "includeVideo": self.include_video,
            "acceptDialogs": self.accept_dialogs,
            "sessionId": self.session_id,
            "callbackUrl": self.callback_url,
            "browserCommands": self.browser_commands.to_wire(),
        }


@dataclass(slots=True)
class SupportedCountryResponse:
    """Represents a country supported for proxy geolocation.

    Attributes:
        name: The full name of the country.
        key: The three-letter country key used for the
            :attr:`~scrapi_sdk.models.ScrapeRequest.proxy_country` option.
        proxy_count: The number of proxies available in this country.
    """

    name: str
    key: str
    proxy_count: int

    @staticmethod
    def from_api_dict(data: Mapping[str, Any]) -> SupportedCountryResponse:
        """Deserialize a :class:`SupportedCountryResponse` from an API response dictionary.

        Args:
            data: A mapping containing the raw API response fields.

        Returns:
            A populated :class:`SupportedCountryResponse` instance.
        """
        return SupportedCountryResponse(
            name=str(data.get("name", data.get("name", ""))),
            key=str(data.get("key", data.get("key", ""))),
            proxy_count=int(data.get("proxyCount", data.get("proxy_count", 0)) or 0),
        )


@dataclass(slots=True)
class SupportedCityResponse:
    """Represents a city supported for proxy geolocation.

    Attributes:
        name: The full name of the city.
        key: The city key used for the
            :attr:`~scrapi_sdk.models.ScrapeRequest.proxy_city` option.
        proxy_count: The number of proxies available in this city.
    """

    name: str
    key: str
    proxy_count: int

    @staticmethod
    def from_api_dict(data: Mapping[str, Any]) -> SupportedCityResponse:
        """Deserialize a :class:`SupportedCityResponse` from an API response dictionary.

        Args:
            data: A mapping containing the raw API response fields.

        Returns:
            A populated :class:`SupportedCityResponse` instance.
        """
        return SupportedCityResponse(
            name=str(data.get("name", data.get("name", ""))),
            key=str(data.get("key", data.get("key", ""))),
            proxy_count=int(data.get("proxyCount", data.get("proxy_count", 0)) or 0),
        )


@dataclass(slots=True)
class BalanceResponse:
    """Represents your ScrAPI credit balance.

    Attributes:
        credits: The number of credits available for the API key.
    """

    credits: int

    @staticmethod
    def from_api_dict(data: Mapping[str, Any]) -> BalanceResponse:
        """Deserialize a :class:`BalanceResponse` from an API response dictionary.

        Args:
            data: A mapping containing the raw API response fields.

        Returns:
            A populated :class:`BalanceResponse` instance.
        """
        return BalanceResponse(credits=int(data.get("credits", data.get("credits", 0)) or 0))


@dataclass(slots=True)
class ScrapeResponse:
    """A web scrape response.

    Attributes:
        request_url: The URL that was requested.
        response_url: The final URL the scraped content was served from, which
            may differ from ``request_url`` if a redirect occurred.
        duration: The total duration of the scrape operation.
        attempts: The number of attempts (including retries) made before a
            response was obtained.
        captchas_solved: A mapping of captcha type to the number of times that
            type was solved successfully during the request.
        credits_used: The number of credits consumed for this scrape operation.
        error_messages: Any error messages reported as a result of failing to
            scrape the content, or ``None`` if the operation succeeded.
        status_code: The final HTTP status code of the scrape operation.
        cookies: Key/value pairs of cookies returned in the response. These
            can be reused in subsequent requests to mimic a session.
        headers: Key/value pairs of headers returned in the response.
        content: The HTML or JSON content of the URL that was scraped.
        screenshot_url: A URL to the screenshot image file, if
            :attr:`~scrapi_sdk.models.ScrapeRequest.include_screenshot` was
            requested.
        pdf_url: A URL to the PDF file, if
            :attr:`~scrapi_sdk.models.ScrapeRequest.include_pdf` was requested.
        video_url: A URL to the video recording file, if
            :attr:`~scrapi_sdk.models.ScrapeRequest.include_video` was requested.
    """

    request_url: str
    response_url: str | None = None
    duration: str | int | float | None = None
    attempts: int = 0
    captchas_solved: dict[str, int] = field(default_factory=dict)
    credits_used: int = 0
    error_messages: list[str] | None = None
    status_code: int = 0
    cookies: dict[str, str] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    content: str | None = None
    screenshot_url: str | None = None
    pdf_url: str | None = None
    video_url: str | None = None

    _html_cache: Any = field(default=None, init=False, repr=False)
    _html_cache_key: str | None = field(default=None, init=False, repr=False)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "content":
            object.__setattr__(self, "_html_cache", None)
            object.__setattr__(self, "_html_cache_key", None)
        object.__setattr__(self, name, value)

    @property
    def content_hash(self) -> str:
        """A SHA-1 hex digest of the content, useful for detecting page changes.

        The hash is computed over the UTF-16 LE encoded bytes of
        :attr:`content`, matching the algorithm used by the C# SDK.

        Returns:
            An uppercase hex string, or an empty string if
            :attr:`content` is empty.
        """
        if not self.content:
            return ""

        digest = hashlib.sha1(self.content.encode("utf-16le"), usedforsecurity=False).hexdigest()
        return digest.upper()

    @property
    def html(self) -> Any:
        """The parsed HTML document, usable for querying content with BeautifulSoup.

        Parses :attr:`content` on first access and caches the result. The cache
        is invalidated automatically when :attr:`content` changes.

        Returns:
            A :class:`bs4.BeautifulSoup` object, or ``None`` if
            :attr:`content` is empty.

        Raises:
            ImportError: If the optional ``beautifulsoup4`` dependency is not
                installed. Install it with
                ``pip install scrapi-sdk[html]``.
        """
        if not self.content:
            return None

        if self._html_cache_key == self.content and self._html_cache is not None:
            return self._html_cache

        try:
            from bs4 import BeautifulSoup
        except ImportError as exc:
            raise ImportError(
                "Install the optional html dependencies first: pip install scrapi-sdk[html]"
            ) from exc

        self._html_cache = BeautifulSoup(html.unescape(self.content), "html.parser")
        self._html_cache_key = self.content
        return self._html_cache

    @staticmethod
    def from_api_dict(data: Mapping[str, Any]) -> ScrapeResponse:
        """Deserialize a :class:`ScrapeResponse` from an API response dictionary.

        Args:
            data: A mapping containing the raw API response fields.

        Returns:
            A populated :class:`ScrapeResponse` instance.
        """
        response = ScrapeResponse(
            request_url=str(data.get("requestUrl", data.get("request_url", ""))),
            response_url=data.get("responseUrl", data.get("response_url")),
            duration=data.get("duration", data.get("duration")),
            attempts=int(data.get("attempts", data.get("attempts", 0)) or 0),
            captchas_solved={
                str(k): int(v)
                for k, v in (data.get("captchasSolved", data.get("captchas_solved", {})) or {}).items()
            },
            credits_used=int(data.get("creditsUsed", data.get("credits_used", 0)) or 0),
            error_messages=[
                str(x) for x in (data.get("errorMessages", data.get("error_messages")) or [])
            ]
            or None,
            status_code=int(data.get("statusCode", data.get("status_code", 0)) or 0),
            cookies={
                str(k): str(v)
                for k, v in (data.get("cookies", data.get("cookies", {})) or {}).items()
            },
            headers={
                str(k): str(v)
                for k, v in (data.get("headers", data.get("headers", {})) or {}).items()
            },
            content=data.get("content", data.get("content")),
            screenshot_url=data.get("screenshotUrl", data.get("screenshot_url")),
            pdf_url=data.get("pdfUrl", data.get("pdf_url")),
            video_url=data.get("videoUrl", data.get("video_url")),
        )

        return response


def parse_proxy_type(value: Any) -> ProxyType:
    return proxy_type_from_wire(value)


def parse_response_format(value: Any) -> ResponseFormat:
    return response_format_from_wire(value)
