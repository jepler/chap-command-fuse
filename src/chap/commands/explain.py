# SPDX-FileCopyrightText: 2023 Jeff Epler <jepler@gmail.com>
#
# SPDX-License-Identifier: MIT

import asyncio
import sys

import click
import rich

from ..session import Session  # pylint: disable=relative-beyond-top-level

bold = "\033[1m"
nobold = "\033[m"


def ipartition(s, sep):
    rest = s
    while rest:
        first, opt_sep, rest = rest.partition(sep)
        yield (first, opt_sep)


class DumbPrinter:
    def raw(self, s):
        pass

    def add(self, s):
        print(s, end="")


class WrappingPrinter:
    def __init__(self, width=None):
        self._width = width or rich.get_console().width
        self._column = 0
        self._line = ""
        self._sp = ""

    def raw(self, s):
        print(s, end="")

    def add(self, s):
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

    def finish(self):
        if self._line:
            self.add("\n")


def verbose_ask(api, session, q):
    if sys.stdout.isatty():
        printer = WrappingPrinter()
    else:
        printer = DumbPrinter()

    async def work():
        async for token in api.aask(session, q):
            printer.add(token)

    asyncio.run(work())
    printer.finish()


@click.command
@click.pass_obj
@click.argument("prompt", nargs=-1, required=True)
def main(obj, prompt):
    """Explain a Unix system command"""
    session = Session.new_session("Explain the following Unix system command")
    api = obj.api

    #    symlink_session_filename(session_filename)

    verbose_ask(api, session, " ".join(prompt))


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
