from __future__ import annotations

from .enums import ProxyType, ResponseFormat


class ScrapeRequestDefaults:
    """Default values applied to :class:`~scrapi_sdk.models.ScrapeRequest` instances.

    These defaults mirror the server-side defaults. All attributes are
    class-level constants and can be referenced when building requests.

    Attributes:
        response_format: Defaults to :attr:`~scrapi_sdk.enums.ResponseFormat.JSON`.
        response_selector: Defaults to ``None``.
        cookies: Defaults to an empty dictionary.
        headers: Defaults to an empty dictionary.
        request_method: Defaults to ``"GET"``.
        proxy_type: Defaults to :attr:`~scrapi_sdk.enums.ProxyType.NONE`.
        proxy_country: Defaults to ``None``.
        proxy_city: Defaults to ``None``.
        custom_proxy_url: Defaults to ``None``.
        use_browser: Defaults to ``False``.
        solve_captchas: Defaults to ``False``.
        include_screenshot: Defaults to ``False``.
        include_pdf: Defaults to ``False``.
        include_video: Defaults to ``False``.
        accept_dialogs: Defaults to ``False``.
        session_id: Defaults to ``None``.
        callback_url: Defaults to ``None``.
    """

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
