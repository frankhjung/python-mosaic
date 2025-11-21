#!/usr/bin/env make

.DEFAULT_GOAL := all

.PHONY: all check clean help run test version

COMMA	:= ,
EMPTY	:=
PYTHON	:= $(shell which python3)
CTAGS	:= $(shell which ctags)

SRCS	:= $(wildcard *.py **/*.py)

all:	check test run

help:
	@echo
	@echo "Default goal: ${.DEFAULT_GOAL}"
	@echo "  all:     default target to build project"
	@echo "  check:   check style and lint code"
	@echo "  run:     run against test data"
	@echo "  test:    run unit tests"
	@echo "  clean:   delete all generated files"
	@echo

check:
ifdef CTAGS
	# ctags for vim
	ctags --recurse -o tags $(SRCS)
endif
	# format with ruff
	uv run ruff format $(SRCS)
	# check with ruff
	uv run ruff check --fix $(SRCS)

test:
	uv run pytest -v tests/test*.py

run:
	uv run python -m mosaic -h

version:
	uv run python -m mosaic --version

clean:
	# clean build distribution
	$(RM) -rf __pycache__ **/__pycache__
	$(RM) -rf python_*.egg-info/
	$(RM) -v *.pyc *.pyo
	$(RM) -v **/*.pyc **/*.pyo
	$(RM) -rf .venv
