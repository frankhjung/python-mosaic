#!/usr/bin/env make

.DEFAULT_GOAL := all

.PHONY: all check clean example help run test version

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
	uv run pytest -v tests/test_*.py

run:
	uv run python -m mosaic -h

example:
	# input image: test.jpg (561 x 422)
	# output image: test_mosaic.jpg (1600 x 2000)
	# tile directory: images
	# output size: 2000
	# tile size: 50
	uv run python -m mosaic \
		-i test.jpg \
		-o test_mosaic.jpg \
		-d images \
		-s 2000 \
		-t 50

version:
	uv run python -m mosaic --version

clean:
	# clean build distribution
	$(RM) -rf __pycache__ **/__pycache__
	$(RM) -rf python_*.egg-info/
	$(RM) -v *.pyc *.pyo
	$(RM) -v **/*.pyc **/*.pyo
	$(RM) -rf .venv/
	$(RM) -rf public/
