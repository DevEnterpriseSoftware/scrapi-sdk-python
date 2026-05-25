from __future__ import annotations

import re
from typing import Any


def numbers_only(text: str | None, include_decimal_points: bool = False, trim: bool = True) -> str:
    """Extract only numeric characters from a string.

    Args:
        text: The input string to process.
        include_decimal_points: When ``True``, decimal points (``.``) are
            preserved in the result. Defaults to ``False``.
        trim: When ``True``, leading and trailing whitespace is stripped from
            the result. Defaults to ``True``.

    Returns:
        A string containing only the numeric characters (and optionally
        decimal points) from ``text``, or an empty string if ``text`` is
        ``None`` or empty.
    """
    if not text:
        return ""

    result = re.sub(r"([^\d\.])*", "", text)
    if not include_decimal_points:
        result = result.replace(".", "")

    return result.strip() if trim else result


def html_with_no_script(html: str | None) -> str:
    """Remove all ``<script>`` elements from an HTML string.

    Args:
        html: The HTML string to process.

    Returns:
        The HTML string with all ``<script>`` blocks removed, or an empty
        string if ``html`` is ``None`` or empty.
    """
    if not html:
        return ""

    return re.sub(
        r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>",
        "",
        html,
        flags=re.IGNORECASE,
    )


def next_element(node: Any) -> Any:
    """Return the next sibling element node, skipping non-element nodes.

    Navigates the BeautifulSoup node tree forward through siblings until
    an element node (one with a ``name`` attribute) is found.

    Args:
        node: A BeautifulSoup node to start from.

    Returns:
        The next sibling element node, or ``None`` if no such sibling exists
        or ``node`` is ``None``.
    """
    if node is None:
        return None

    sibling = node.next_sibling
    while sibling is not None:
        if getattr(sibling, "name", None) is not None:
            return sibling
        sibling = sibling.next_sibling

    return None


def is_visible(node: Any, check_parent_nodes: bool = True) -> bool:
    """Determine whether a BeautifulSoup node is visually visible.

    Inspects the ``style`` attribute of the node (and, optionally, its
    ancestor nodes) for CSS rules that would hide the element, such as
    ``display: none`` or ``visibility: hidden``.

    Args:
        node: A BeautifulSoup node to inspect.
        check_parent_nodes: When ``True``, the visibility of all ancestor
            nodes is also checked recursively. Defaults to ``True``.

    Returns:
        ``True`` if the node (and all its ancestors when
        ``check_parent_nodes`` is ``True``) appears to be visible;
        ``False`` otherwise or if ``node`` is ``None``.
    """
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
