#!/usr/bin/env make

.DEFAULT_GOAL := all

.PHONY: all check clean example help run test version

COMMA	:= ,
EMPTY	:=
PYTHON	:= $(shell which python3)
CTAGS	:= $(shell which ctags)

SRCS	:= $(wildcard *.py **/*.py)

all: check test run ## Check, test, and run the project

.PHONY: help
help: ## Display this help
	@printf "Default goal: \033[36m%s\033[0m\n" "${.DEFAULT_GOAL}"
	@awk 'BEGIN {FS = ":.*##"; \
	  printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} \
	    /^[a-zA-Z_-]+:.*?##/ \
	    { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 }' \
	  $(MAKEFILE_LIST)

check: ## Check style and lint code
ifdef CTAGS
	# ctags for vim
	ctags --recurse -o tags $(SRCS)
endif
	# format with ruff
	uv run ruff format $(SRCS)
	# check with ruff
	uv run ruff check --fix $(SRCS)

test: ## Run unit tests
	uv run pytest -v tests/test_*.py

run: ## Run against test data
	uv run python -m mosaic -h

example: ## Run a full example mosaic build
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

version: ## Print the package version
	uv run python -m mosaic --version

clean: ## Delete all generated files
	# clean build distribution
	$(RM) -rf __pycache__ **/__pycache__
	$(RM) -rf python_*.egg-info/
	$(RM) -v *.pyc *.pyo
	$(RM) -v **/*.pyc **/*.pyo
	$(RM) -rf .venv/
	$(RM) -rf public/
