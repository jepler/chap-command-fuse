# SPDX-FileCopyrightText: 2023 Jeff Epler <jepler@gmail.com>
#
# SPDX-License-Identifier: MIT

import collections
import errno
import os
import stat

import click
import fuse  # type: ignore
import platformdirs
from fuse import Fuse  # type: ignore

from ..core import Obj  # pylint: disable=relative-beyond-top-level
from ..session import new_session  # pylint: disable=relative-beyond-top-level

fuse.fuse_python_api = (0, 2)


class MyStat(fuse.Stat):
    def __init__(self):
        self.st_mode = 0
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 0
        self.st_uid = 0
        self.st_gid = 0
        self.st_size = 0
        self.st_atime = 0
        self.st_mtime = 0
        self.st_ctime = 0


def gather_prompts():
    result = {}
    prompts_dir = platformdirs.user_config_path("chap") / "fuse_prompts"
    for path in prompts_dir.glob("*.txt"):
        result[path.stem] = path.read_text(encoding="utf-8")
    return result


def split_path(p):
    if p == "/":
        return []
    return p.split("/")[1:]


class ChapFS(Fuse):
    def __init__(self, api, *args, **kw):
        usage = (
            """
Serve LLM responses in a filesystem

"""
            + Fuse.fusage
        )
        super().__init__(
            version="chap fuse {fuse.__version__}", usage=usage, dash_s_do="setsingle"
        )
        self.api = api
        self.prompts = gather_prompts()
        print("PROMPTS", self.prompts)
        self.cached = collections.defaultdict(dict)

    def getattr(self, path):
        st = MyStat()
        parts = split_path(path)
        print("getattr", path, parts)
        if len(parts) <= 1:
            st.st_mode = stat.S_IFDIR | 0o755
            st.st_nlink = 2
        elif len(parts) == 2:
            prompt, query = parts
            if prompt not in self.prompts:
                return -errno.ENOENT
            c = self.ask(self.prompts[prompt], query).encode("utf-8")
            st.st_mode = stat.S_IFREG | 0o444
            st.st_nlink = 1
            st.st_size = len(c)
        else:
            return -errno.ENOENT
        return st

    def readdir(self, path, offset):
        parts = split_path(path)
        print("readdir", path, parts)
        for r in ".", "..":
            yield fuse.Direntry(r)
        if len(parts) == 0:
            for p in self.prompts:
                print("READDIR prompt", p)
                yield fuse.Direntry(p)
        elif len(parts) == 1:
            for c in self.cached[parts[0]]:
                yield fuse.Direntry(c)

    def open(self, path, flags):
        parts = split_path(path)
        print("open", path, parts)
        if len(parts) != 2:
            print("incorrect parts len ***")
            return -errno.ENOENT
        prompt, query = parts
        if prompt not in self.prompts:
            print("not in prompts !!!")
            return -errno.ENOENT
        accmode = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
        if (flags & accmode) != os.O_RDONLY:
            return -errno.EACCES

    def read(self, path, size, offset):
        parts = split_path(path)
        if len(parts) != 2:
            print("incorrect parts len ***", len(parts))
            return -errno.ENOENT
        prompt, query = parts
        if prompt not in self.prompts:
            print("not in prompts !!!")
            return -errno.ENOENT

        c = self.ask(self.prompts[prompt], query).encode("utf-8")
        return c[offset : offset + size]

    def ask(self, system_prompt, query):
        cache = self.cached[system_prompt]
        c = cache.get(query, None)
        if c is None:
            session = new_session(system_prompt)
            c = self.api.ask(session, query)
            lines = c.splitlines()
            if lines and lines[0].startswith("```"):
                del lines[0]
            if lines and lines[-1].startswith("```"):
                del lines[-1]
            c = "\n".join(lines) + "\n"
            cache[query] = c
        return c


@click.command(
    context_settings=dict(
        ignore_unknown_options=True,
    )
)
@click.pass_obj
@click.argument("fuse-args", nargs=-1, required=True)
def main(obj: Obj, fuse_args: str) -> None:
    """Explain a Unix system command"""
    api = obj.api
    assert api is not None
    server = ChapFS(api)
    server.parse(["chap-fuse"] + list(fuse_args), errex=1)
    server.main()


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
