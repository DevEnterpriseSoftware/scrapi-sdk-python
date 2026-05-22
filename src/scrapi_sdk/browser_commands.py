from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Union


class BrowserCommand:
    command_name: str

    def to_wire(self) -> dict[str, Any]:
        raise NotImplementedError


@dataclass(slots=True)
class ClickCommand(BrowserCommand):
    target_selector: str = ""
    command_name: str = "click"

    def to_wire(self) -> dict[str, Any]:
        return {self.command_name: self.target_selector}


@dataclass(slots=True)
class ScrollCommand(BrowserCommand):
    pixels: int = 1000
    command_name: str = "scroll"

    def to_wire(self) -> dict[str, Any]:
        return {self.command_name: self.pixels}


@dataclass(slots=True)
class WaitCommand(BrowserCommand):
    milliseconds: int = 0
    command_name: str = "wait"

    def to_wire(self) -> dict[str, Any]:
        return {self.command_name: self.milliseconds}


@dataclass(slots=True)
class WaitForCommand(BrowserCommand):
    target_selector: str = ""
    command_name: str = "wait_for"

    def to_wire(self) -> dict[str, Any]:
        return {self.command_name: self.target_selector}


@dataclass(slots=True)
class InputCommand(BrowserCommand):
    target_selector: str = ""
    input_value: str = ""
    command_name: str = "input"

    def to_wire(self) -> dict[str, Any]:
        return {self.command_name: {self.target_selector: self.input_value}}


@dataclass(slots=True)
class SelectCommand(BrowserCommand):
    target_selector: str = ""
    select_value: str = ""
    command_name: str = "select"

    def to_wire(self) -> dict[str, Any]:
        return {self.command_name: {self.target_selector: self.select_value}}


@dataclass(slots=True)
class JavaScriptCommand(BrowserCommand):
    script: str = ""
    command_name: str = "javascript"

    def to_wire(self) -> dict[str, Any]:
        return {self.command_name: self.script}


BrowserCommandType = Union[ClickCommand, ScrollCommand, WaitCommand, WaitForCommand, InputCommand, SelectCommand, JavaScriptCommand]


class BrowserCommandList(list[BrowserCommandType]):
    def click(self, target_selector: str) -> BrowserCommandList:
        self.append(ClickCommand(target_selector=target_selector))
        return self

    def scroll(self, pixels: int = 1000) -> BrowserCommandList:
        self.append(ScrollCommand(pixels=pixels))
        return self

    def wait(self, milliseconds: int) -> BrowserCommandList:
        if milliseconds > 15000:
            raise ValueError("The maximum wait time is 15 seconds.")

        self.append(WaitCommand(milliseconds=milliseconds))
        return self

    def wait_for(self, target_selector: str) -> BrowserCommandList:
        self.append(WaitForCommand(target_selector=target_selector))
        return self

    def input(self, target_selector: str, input_value: str) -> BrowserCommandList:
        self.append(InputCommand(target_selector=target_selector, input_value=input_value))
        return self

    def select(self, target_selector: str, select_value: str) -> BrowserCommandList:
        self.append(SelectCommand(target_selector=target_selector, select_value=select_value))
        return self

    def evaluate(self, javascript: str) -> BrowserCommandList:
        self.append(JavaScriptCommand(script=javascript))
        return self

    def to_wire(self) -> list[dict[str, Any]]:
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

