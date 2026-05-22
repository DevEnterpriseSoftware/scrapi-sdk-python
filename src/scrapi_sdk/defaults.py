from __future__ import annotations

from .enums import ProxyType, ResponseFormat


class ScrapeRequestDefaults:
    response_format: ResponseFormat = ResponseFormat.JSON
    response_selector: str | None = None
    cookies: dict[str, str] = {}
    headers: dict[str, str] = {}
    request_method: str = "GET"
    proxy_type: ProxyType = ProxyType.NONE
    proxy_country: str | None = None
    proxy_city: str | None = None
    custom_proxy_url: str | None = None
    use_browser: bool = False
    solve_captchas: bool = False
    include_screenshot: bool = False
    include_pdf: bool = False
    include_video: bool = False
    accept_dialogs: bool = False
    session_id: str | None = None
    callback_url: str | None = None
