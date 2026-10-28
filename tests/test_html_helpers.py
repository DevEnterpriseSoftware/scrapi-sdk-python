from scrapi_sdk.html_helpers import html_with_no_script


def test_html_with_no_script_removes_script_blocks() -> None:
    html = "<p>safe</p><script>alert(1)</script><p>after</p>"

    assert html_with_no_script(html) == "<p>safe</p><p>after</p>"


def test_html_with_no_script_handles_whitespace_in_end_tag() -> None:
    html = "<p>safe</p><script>alert(1)</script ><p>after</p>"

    result = html_with_no_script(html)

    assert "alert(1)" not in result
    assert "<script" not in result.lower()
    assert result == "<p>safe</p><p>after</p>"


def test_html_with_no_script_handles_attributes_and_case() -> None:
    html = '<SCRIPT type="text/javascript" src="evil.js"></SCRIPT><p>safe</p>'

    assert html_with_no_script(html) == "<p>safe</p>"


def test_html_with_no_script_removes_nested_script_markup() -> None:
    html = "<script><script>alert(1)</script></script><p>safe</p>"

    result = html_with_no_script(html)

    assert "alert(1)" not in result
    assert "<script" not in result.lower()
    assert "<p>safe</p>" in result


def test_html_with_no_script_returns_empty_for_falsy_input() -> None:
    assert html_with_no_script(None) == ""
    assert html_with_no_script("") == ""
