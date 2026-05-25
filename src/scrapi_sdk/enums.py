from __future__ import annotations

from enum import IntEnum


class ProxyType(IntEnum):
    """Proxy type options to use when requesting a scrape operation."""

    #: No proxy will be used (default). Fastest option but can be blocked by
    #: sites that throttle traffic.
    NONE = 0

    #: A rotating public/free proxy will be used. Uses free anonymous proxies
    #: from the internet; generally slow and unreliable. Not recommended for
    #: production workloads.
    FREE = 1

    #: A rotating residential proxy will be used. Slower but more reliable for
    #: sites that actively try to block scraping activity.
    RESIDENTIAL = 2

    #: A rotating data center proxy will be used. Faster but can be less
    #: reliable on sites that try to block scraping activity.
    DATACENTER = 3

    #: A Tor proxy will be used. Ideal for scraping Onion websites.
    TOR = 4

    #: A custom proxy will be used. Configure the URL via
    #: :attr:`~scrapi_sdk.models.ScrapeRequest.custom_proxy_url`.
    CUSTOM = 5


class ResponseFormat(IntEnum):
    """Response format options for a scrape operation."""

    #: Standard JSON response representing a
    #: :class:`~scrapi_sdk.models.ScrapeResponse` object.
    #: Content type: ``application/json``.
    JSON = 0

    #: HTML response; other information is returned as headers.
    #: Content type: ``text/html``.
    HTML = 1

    #: Markdown response; other information is returned as headers.
    #: Content type: ``text/markdown``.
    MARKDOWN = 2


_PROXY_TYPE_WIRE = {
    ProxyType.NONE: "None",
    ProxyType.FREE: "Free",
    ProxyType.RESIDENTIAL: "Residential",
    ProxyType.DATACENTER: "DataCenter",
    ProxyType.TOR: "Tor",
    ProxyType.CUSTOM: "Custom",
}

_RESPONSE_FORMAT_WIRE = {
    ResponseFormat.JSON: "Json",
    ResponseFormat.HTML: "Html",
    ResponseFormat.MARKDOWN: "Markdown",
}


def proxy_type_to_wire(value: ProxyType) -> str:
    return _PROXY_TYPE_WIRE[value]


def proxy_type_from_wire(value: object) -> ProxyType:
    if isinstance(value, ProxyType):
        return value

    if isinstance(value, int):
        return ProxyType(value)

    text = str(value or "").strip().lower()
    mapping = {
        "none": ProxyType.NONE,
        "free": ProxyType.FREE,
        "residential": ProxyType.RESIDENTIAL,
        "datacenter": ProxyType.DATACENTER,
        "data_center": ProxyType.DATACENTER,
        "data-center": ProxyType.DATACENTER,
        "tor": ProxyType.TOR,
        "custom": ProxyType.CUSTOM,
    }
    if text not in mapping:
        raise ValueError(f"Unknown proxy type: {value}")

    return mapping[text]


def response_format_to_wire(value: ResponseFormat) -> str:
    return _RESPONSE_FORMAT_WIRE[value]


def response_format_from_wire(value: object) -> ResponseFormat:
    if isinstance(value, ResponseFormat):
        return value

    if isinstance(value, int):
        return ResponseFormat(value)

    text = str(value or "").strip().lower()
    mapping = {
        "json": ResponseFormat.JSON,
        "html": ResponseFormat.HTML,
        "markdown": ResponseFormat.MARKDOWN,
    }
    if text not in mapping:
        raise ValueError(f"Unknown response format: {value}")

    return mapping[text]
