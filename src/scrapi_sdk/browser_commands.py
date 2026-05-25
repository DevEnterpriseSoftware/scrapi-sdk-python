from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Union


class BrowserCommand:
    """Base class for browser commands executed after a page has loaded.

    Browser commands allow automated interaction with a web page when
    :attr:`~scrapi_sdk.models.ScrapeRequest.use_browser` is set to ``True``.
    Commands are executed in the order they are added to the request.
    """

    command_name: str
    """The command name that identifies the type of browser command."""

    def to_wire(self) -> dict[str, Any]:
        """Serialize this command to its API wire representation.

        Returns:
            A dictionary containing the command payload for the ScrAPI API.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError


@dataclass(slots=True)
class ClickCommand(BrowserCommand):
    """Browser command that clicks an element on the page.

    Attributes:
        target_selector: The CSS or XPath selector used to find the element to click.
        command_name: The wire command name. Always ``"click"``.
    """

    target_selector: str = ""
    command_name: str = "click"

    def to_wire(self) -> dict[str, Any]:
        """Serialize the click command to its API wire representation.

        Returns:
            A dictionary mapping ``"click"`` to the target selector.
        """
        return {self.command_name: self.target_selector}


@dataclass(slots=True)
class ScrollCommand(BrowserCommand):
    """Browser command that scrolls the page by a number of pixels.

    Attributes:
        pixels: The number of pixels to scroll. Use negative values to scroll up.
            Defaults to 1000.
        command_name: The wire command name. Always ``"scroll"``.
    """

    pixels: int = 1000
    command_name: str = "scroll"

    def to_wire(self) -> dict[str, Any]:
        """Serialize the scroll command to its API wire representation.

        Returns:
            A dictionary mapping ``"scroll"`` to the pixel count.
        """
        return {self.command_name: self.pixels}


@dataclass(slots=True)
class WaitCommand(BrowserCommand):
    """Browser command that pauses execution for a fixed duration.

    Attributes:
        milliseconds: The number of milliseconds to wait. Maximum is 15000.
        command_name: The wire command name. Always ``"wait"``.
    """

    milliseconds: int = 0
    command_name: str = "wait"

    def to_wire(self) -> dict[str, Any]:
        """Serialize the wait command to its API wire representation.

        Returns:
            A dictionary mapping ``"wait"`` to the millisecond duration.
        """
        return {self.command_name: self.milliseconds}


@dataclass(slots=True)
class WaitForCommand(BrowserCommand):
    """Browser command that waits until a specific element is present on the page.

    Attributes:
        target_selector: The CSS or XPath selector used to find the target element.
        command_name: The wire command name. Always ``"wait_for"``.
    """

    target_selector: str = ""
    command_name: str = "wait_for"

    def to_wire(self) -> dict[str, Any]:
        """Serialize the wait-for command to its API wire representation.

        Returns:
            A dictionary mapping ``"wait_for"`` to the target selector.
        """
        return {self.command_name: self.target_selector}


@dataclass(slots=True)
class InputCommand(BrowserCommand):
    """Browser command that types text into an input element.

    Attributes:
        target_selector: The CSS or XPath selector used to find the input element.
        input_value: The text value to enter into the target element.
        command_name: The wire command name. Always ``"input"``.
    """

    target_selector: str = ""
    input_value: str = ""
    command_name: str = "input"

    def to_wire(self) -> dict[str, Any]:
        """Serialize the input command to its API wire representation.

        Returns:
            A dictionary mapping ``"input"`` to a selector/value pair.
        """
        return {self.command_name: {self.target_selector: self.input_value}}


@dataclass(slots=True)
class SelectCommand(BrowserCommand):
    """Browser command that selects an option from a ``<select>`` element.

    Attributes:
        target_selector: The CSS or XPath selector used to find the ``<select>`` element.
        select_value: The option value to select on the target element.
        command_name: The wire command name. Always ``"select"``.
    """

    target_selector: str = ""
    select_value: str = ""
    command_name: str = "select"

    def to_wire(self) -> dict[str, Any]:
        """Serialize the select command to its API wire representation.

        Returns:
            A dictionary mapping ``"select"`` to a selector/value pair.
        """
        return {self.command_name: {self.target_selector: self.select_value}}


@dataclass(slots=True)
class JavaScriptCommand(BrowserCommand):
    """Browser command that evaluates a JavaScript snippet on the page.

    Attributes:
        script: The JavaScript snippet to execute. Subject to a 5-second execution limit.
        command_name: The wire command name. Always ``"javascript"``.
    """

    script: str = ""
    command_name: str = "javascript"

    def to_wire(self) -> dict[str, Any]:
        """Serialize the JavaScript command to its API wire representation.

        Returns:
            A dictionary mapping ``"javascript"`` to the script string.
        """
        return {self.command_name: self.script}


BrowserCommandType = Union[ClickCommand, ScrollCommand, WaitCommand, WaitForCommand, InputCommand, SelectCommand, JavaScriptCommand]


class BrowserCommandList(list[BrowserCommandType]):
    """An ordered list of browser commands to execute after a page has loaded.

    Provides a fluent interface for building sequences of browser interactions.
    All methods return ``self`` to allow chaining.

    Example::

        request.browser_commands \\
            .click("#accept-cookies") \\
            .wait(500) \\
            .input("#search", "example query") \\
            .click("#submit")
    """

    def click(self, target_selector: str) -> BrowserCommandList:
        """Append a click command targeting the specified element.

        Args:
            target_selector: The CSS or XPath selector of the element to click.

        Returns:
            This :class:`BrowserCommandList` instance for chaining.
        """
        self.append(ClickCommand(target_selector=target_selector))
        return self

    def scroll(self, pixels: int = 1000) -> BrowserCommandList:
        """Append a scroll command to scroll the page by the given number of pixels.

        Args:
            pixels: The number of pixels to scroll. Use a negative value to scroll
                up. Defaults to 1000.

        Returns:
            This :class:`BrowserCommandList` instance for chaining.
        """
        self.append(ScrollCommand(pixels=pixels))
        return self

    def wait(self, milliseconds: int) -> BrowserCommandList:
        """Append a wait command to pause execution for the given duration.

        Args:
            milliseconds: The number of milliseconds to wait. Maximum is 15000.

        Returns:
            This :class:`BrowserCommandList` instance for chaining.

        Raises:
            ValueError: If ``milliseconds`` exceeds 15000.
        """
        if milliseconds > 15000:
            raise ValueError("The maximum wait time is 15 seconds.")

        self.append(WaitCommand(milliseconds=milliseconds))
        return self

    def wait_for(self, target_selector: str) -> BrowserCommandList:
        """Append a command that waits until the specified element is present.

        Args:
            target_selector: The CSS or XPath selector of the element to wait for.

        Returns:
            This :class:`BrowserCommandList` instance for chaining.
        """
        self.append(WaitForCommand(target_selector=target_selector))
        return self

    def input(self, target_selector: str, input_value: str) -> BrowserCommandList:
        """Append a command that types text into the specified input element.

        Args:
            target_selector: The CSS or XPath selector of the input element.
            input_value: The text value to enter into the element.

        Returns:
            This :class:`BrowserCommandList` instance for chaining.
        """
        self.append(InputCommand(target_selector=target_selector, input_value=input_value))
        return self

    def select(self, target_selector: str, select_value: str) -> BrowserCommandList:
        """Append a command that selects an option from a ``<select>`` element.

        Args:
            target_selector: The CSS or XPath selector of the ``<select>`` element.
            select_value: The option value to select.

        Returns:
            This :class:`BrowserCommandList` instance for chaining.
        """
        self.append(SelectCommand(target_selector=target_selector, select_value=select_value))
        return self

    def evaluate(self, javascript: str) -> BrowserCommandList:
        """Append a command that evaluates a JavaScript snippet on the page.

        Args:
            javascript: The JavaScript snippet to execute. Subject to a 5-second
                execution limit.

        Returns:
            This :class:`BrowserCommandList` instance for chaining.
        """
        self.append(JavaScriptCommand(script=javascript))
        return self

    def to_wire(self) -> list[dict[str, Any]]:
        """Serialize all commands in the list to their API wire representation.

        Returns:
            A list of command dictionaries suitable for inclusion in the API request.
        """
        return [command.to_wire() for command in self]


def command_from_wire(item: Mapping[str, Any]) -> BrowserCommandType:
    if len(item) != 1:
        raise ValueError(f"Invalid browser command payload: {item}")

    key = next(iter(item.keys())).strip().lower()
    value = item[next(iter(item.keys()))]

    if key in {"click", "tap"}:
        return ClickCommand(target_selector=str(value or ""))

    if key == "scroll":
        return ScrollCommand(pixels=int(value or 0))

    if key == "wait":
        return WaitCommand(milliseconds=int(value or 0))

    if key in {"waitfor", "wait_for", "wait-for"}:
        return WaitForCommand(target_selector=str(value or ""))

    if key in {"javascript", "js", "eval", "evaluate"}:
        return JavaScriptCommand(script=str(value or ""))

    if key in {"input", "fill", "type"}:
        if isinstance(value, Mapping) and value:
            selector = next(iter(value.keys()))
            return InputCommand(target_selector=str(selector), input_value=str(value[selector]))
        return InputCommand()

    if key in {"select", "choose", "pick"}:
        if isinstance(value, Mapping) and value:
            selector = next(iter(value.keys()))
            return SelectCommand(target_selector=str(selector), select_value=str(value[selector]))
        return SelectCommand()

    raise ValueError(f"Unknown browser command key: {key}")


def commands_from_wire(items: list[Mapping[str, Any]] | None) -> BrowserCommandList:
    commands = BrowserCommandList()
    for item in items or []:
        commands.append(command_from_wire(item))
    return commands

