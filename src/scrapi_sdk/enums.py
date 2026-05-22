from __future__ import annotations

from enum import IntEnum


class ProxyType(IntEnum):
    NONE = 0
    FREE = 1
    RESIDENTIAL = 2
    DATACENTER = 3
    TOR = 4
    CUSTOM = 5


class ResponseFormat(IntEnum):
    JSON = 0
    HTML = 1
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
