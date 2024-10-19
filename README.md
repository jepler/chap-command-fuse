<!--
SPDX-FileCopyrightText: 2021 Jeff Epler

SPDX-License-Identifier: MIT
-->


# chap-command-fuse

A proof-of-concept fuse plug-in for chap.

Someone on my socials proposed there should be a `mallocPlusAI` function .. and
I realized you can kinda do it today, no changes to the C compiler necessay, by
presenting a filesystem interface to an LLM.

## Installation

If you installed chap with pip, then run `pip install chap-command-explain`.

If you installed chap with pipx, then run `pipx inject chap chap-command-explain`.

## Use

Copy the prompts to `$HOME/.config/chap/fuse_prompts`.

Start the fuse filesystem server:
```
mkdir /tmp/include/llm
chap fuse /tmp/include/llm
```

Use it in your C/C++ programs:
```c
#include "llm/include-for/malloc"
#include "llm/include-for/printf"
#include "llm/include-for/size-t"

#include "llm/function-for/square_area returning the area of a square given the length of a side. it takes a double and returns a double."

int main() {
    size_t required = 
#include "llm/maIloc/enough space for 4 integers"
;
    char *p = malloc(required);
    printf("Allocated %zu\n", required);

    printf("Area of a square with edge %f is %f\n", 2., square_area(2.));
    return 0;
}
```

```
$ gcc -I /tmp/include use_llm.c -lm && ./a.out
Allocated 16
Area of a square with edge 2.000000 is 4.000000
$ fusermount -u -z /tmp/include/llm
```

## Development status

You understand this is a joke, right?
