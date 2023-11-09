# SPDX-FileCopyrightText: 2023 Jeff Epler <jepler@gmail.com>
#
# SPDX-License-Identifier: MIT

import asyncio
import sys
from typing import Iterable, Protocol

import click
import rich

from ..core import Backend, Obj  # pylint: disable=relative-beyond-top-level
from ..session import Session, new_session  # pylint: disable=relative-beyond-top-level

bold = "\033[1m"
nobold = "\033[m"


def ipartition(s: str, sep: str) -> Iterable[tuple[str, str]]:
    rest = s
    while rest:
        first, opt_sep, rest = rest.partition(sep)
        yield (first, opt_sep)


class Printable(Protocol):
    def raw(self, s: str) -> None:
        """Print a raw escape code"""

    def add(self, s: str) -> None:
        """Add text to the output"""

    def finish(self) -> None:
        """Print trailing data"""


class DumbPrinter:
    def raw(self, s: str) -> None:
        pass

    def add(self, s: str) -> None:
        print(s, end="")

    def finish(self) -> None:
        pass


class WrappingPrinter:
    def __init__(self, width: int | None = None) -> None:
        self._width = width or rich.get_console().width
        self._column = 0
        self._line = ""
        self._sp = ""

    def raw(self, s: str) -> None:
        print(s, end="")

    def add(self, s: str) -> None:
        for line, opt_nl in ipartition(s, "\n"):
            for word, opt_sp in ipartition(line, " "):
                newlen = len(self._line) + len(self._sp) + len(word)
                if not self._line or (newlen <= self._width):
                    self._line += self._sp + word
                    self._sp = opt_sp
                else:
                    if not self._sp and " " in self._line:
                        old_len = len(self._line)
                        self._line, _, partial = self._line.rpartition(" ")
                        print("\r" + self._line + " " * (old_len - len(self._line)))
                        self._line = partial + word
                    else:
                        print()
                        self._line = word
                    self._sp = opt_sp
                print("\r" + self._line, end="")
            if opt_nl:
                print()
                self._line = ""
                self._sp = ""

    def finish(self) -> None:
        if self._line:
            self.add("\n")


def verbose_ask(api: Backend, session: Session, q: str) -> None:
    printer: Printable
    if sys.stdout.isatty():
        printer = WrappingPrinter()
    else:
        printer = DumbPrinter()

    async def work() -> None:
        async for token in api.aask(session, q):
            printer.add(token)

    asyncio.run(work())
    printer.finish()


@click.command
@click.pass_obj
@click.argument("prompt", nargs=-1, required=True)
def main(obj: Obj, prompt: str) -> None:
    """Explain a Unix system command"""
    session = new_session("Explain the following Unix system command")
    api = obj.api
    assert api is not None

    #    symlink_session_filename(session_filename)

    verbose_ask(api, session, " ".join(prompt))


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
