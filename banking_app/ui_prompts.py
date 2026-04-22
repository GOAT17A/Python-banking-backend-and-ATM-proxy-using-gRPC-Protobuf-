from __future__ import annotations

from typing import Callable, TypeVar

from rich.console import Console
from rich.prompt import Prompt

from banking_app.validation import ValidationError

T = TypeVar("T")


def prompt_validated(console: Console, *, label: str, validator: Callable[[str], T], password: bool = False) -> T:
    while True:
        value = Prompt.ask(label, password=password)
        try:
            return validator(value)
        except ValidationError as exc:
            console.print(f"[red]{exc}[/red]")


def prompt_choice(console: Console, *, label: str, choices: list[str], default: str | None = None) -> str:
    choices_norm = [c.lower() for c in choices]
    default_norm = default.lower() if default else None
    while True:
        value = Prompt.ask(label, choices=choices_norm, default=default_norm)
        return value


def prompt_int_validated(console: Console, *, label: str, validator: Callable[[int], int], default: int | None = None) -> int:
    while True:
        raw = Prompt.ask(label, default=str(default) if default is not None else None)
        raw = raw.strip()
        if not raw.isdigit():
            console.print(f"[red]{label}: must be digits only[/red]")
            continue
        try:
            return validator(int(raw))
        except ValidationError as exc:
            console.print(f"[red]{exc}[/red]")
