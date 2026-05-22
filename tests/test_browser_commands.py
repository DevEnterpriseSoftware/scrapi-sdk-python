import pytest

from scrapi_sdk.browser_commands import (
    BrowserCommandList,
    ClickCommand,
    InputCommand,
    JavaScriptCommand,
    ScrollCommand,
    SelectCommand,
    WaitCommand,
    WaitForCommand,
    commands_from_wire,
)


def test_browser_command_list_serializes_to_expected_wire_shape() -> None:
    commands = (
        BrowserCommandList()
        .input("input[name='name']", "Werner")
        .select("select[name='type']", "Discover")
        .wait(1000)
        .wait_for("button[type='submit']")
        .click("button[type='submit']")
        .scroll(500)
        .evaluate("console.log('done')")
    )

    assert commands.to_wire() == [
        {"input": {"input[name='name']": "Werner"}},
        {"select": {"select[name='type']": "Discover"}},
        {"wait": 1000},
        {"wait_for": "button[type='submit']"},
        {"click": "button[type='submit']"},
        {"scroll": 500},
        {"javascript": "console.log('done')"},
    ]


def test_wait_command_enforces_maximum() -> None:
    commands = BrowserCommandList()

    with pytest.raises(ValueError, match="maximum wait time"):
        commands.wait(15001)


def test_commands_from_wire_supports_aliases() -> None:
    payload = [
        {"tap": "#a"},
        {"fill": {"#b": "x"}},
        {"pick": {"#c": "y"}},
        {"evaluate": "1+1"},
        {"wait-for": "#d"},
        {"scroll": 99},
        {"wait": 50},
    ]

    commands = commands_from_wire(payload)

    assert isinstance(commands[0], ClickCommand)
    assert isinstance(commands[1], InputCommand)
    assert isinstance(commands[2], SelectCommand)
    assert isinstance(commands[3], JavaScriptCommand)
    assert isinstance(commands[4], WaitForCommand)
    assert isinstance(commands[5], ScrollCommand)
    assert isinstance(commands[6], WaitCommand)
