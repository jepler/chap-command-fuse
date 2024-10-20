# SPDX-FileCopyrightText: 2023 Jeff Epler <jepler@gmail.com>
#
# SPDX-License-Identifier: MIT

.PHONY: mypy
mypy: venv/bin/mypy
	venv/bin/mypy -p chap

venv/bin/mypy:
	python -mvenv venv
	venv/bin/pip install chap mypy

.PHONY: clean
clean:
	rm -rf venv
