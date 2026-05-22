from __future__ import annotations

import re
from typing import Any


def numbers_only(text: str | None, include_decimal_points: bool = False, trim: bool = True) -> str:
    if not text:
        return ""

    result = re.sub(r"([^\d\.])*", "", text)
    if not include_decimal_points:
        result = result.replace(".", "")

    return result.strip() if trim else result


def html_with_no_script(html: str | None) -> str:
    if not html:
        return ""

    return re.sub(
        r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>",
        "",
        html,
        flags=re.IGNORECASE,
    )


def next_element(node: Any) -> Any:
    if node is None:
        return None

    sibling = node.next_sibling
    while sibling is not None:
        if getattr(sibling, "name", None) is not None:
            return sibling
        sibling = sibling.next_sibling

    return None


def is_visible(node: Any, check_parent_nodes: bool = True) -> bool:
    if node is None:
        return False

    style = ""
    attrs = getattr(node, "attrs", {})
    if isinstance(attrs, dict):
        style = str(attrs.get("style", ""))

    if not _check_style_visibility(style):
        return False

    parent = getattr(node, "parent", None)
    if check_parent_nodes and parent is not None and getattr(parent, "name", None) is not None:
        return is_visible(parent, True)

    return True


def _check_style_visibility(style: str) -> bool:
    if not style.strip():
        return True

    keys = _parse_html_style_string(style)

    display = keys.get("display")
    if display and display.lower() == "none":
        return False

    visibility = keys.get("visibility")
    if visibility and visibility.lower() == "hidden":
        return False

    return True


def _parse_html_style_string(style: str) -> dict[str, str]:
    result: dict[str, str] = {}

    for segment in style.replace(" ", "").lower().split(";"):
        if not segment or ":" not in segment:
            continue

        key, value = segment.split(":", 1)
        result[key] = value

    return result
