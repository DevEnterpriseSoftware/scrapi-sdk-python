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
        try:
            self.url = normalize_url(self.url)
        except ValueError:
            # Keep invalid values untouched so client validation can return parity messages.
            pass

    def to_api_dict(self) -> dict[str, Any]:
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
    name: str
    key: str
    proxy_count: int

    @staticmethod
    def from_api_dict(data: Mapping[str, Any]) -> SupportedCountryResponse:
        return SupportedCountryResponse(
            name=str(data.get("name", data.get("name", ""))),
            key=str(data.get("key", data.get("key", ""))),
            proxy_count=int(data.get("proxyCount", data.get("proxy_count", 0)) or 0),
        )


@dataclass(slots=True)
class SupportedCityResponse:
    name: str
    key: str
    proxy_count: int

    @staticmethod
    def from_api_dict(data: Mapping[str, Any]) -> SupportedCityResponse:
        return SupportedCityResponse(
            name=str(data.get("name", data.get("name", ""))),
            key=str(data.get("key", data.get("key", ""))),
            proxy_count=int(data.get("proxyCount", data.get("proxy_count", 0)) or 0),
        )


@dataclass(slots=True)
class BalanceResponse:
    credits: int

    @staticmethod
    def from_api_dict(data: Mapping[str, Any]) -> BalanceResponse:
        return BalanceResponse(credits=int(data.get("credits", data.get("credits", 0)) or 0))


@dataclass(slots=True)
class ScrapeResponse:
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
        if not self.content:
            return ""

        digest = hashlib.sha1(self.content.encode("utf-16le"), usedforsecurity=False).hexdigest()
        return digest.upper()

    @property
    def html(self) -> Any:
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
