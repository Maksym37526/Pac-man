# Pac-Man — 42 project
# Subject III.2 requires the rules: install, run, debug, clean, lint.
# lint-strict is optional but recommended.

PYTHON      := python3
VENV        := .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP    := $(VENV)/bin/pip
ENTRY       := pac-man.py
CONFIG      := config.json

# Flags taken verbatim from subject III.2.
MYPY_FLAGS := --warn-return-any \
              --warn-unused-ignores \
              --ignore-missing-imports \
              --disallow-untyped-defs \
              --check-untyped-defs

.PHONY: all install run debug clean lint lint-strict test format help

all: help

## install: create the virtualenv and install every dependency
install:
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	@$(VENV_PIP) install --upgrade pip
	@$(VENV_PIP) install -r requirements.txt
	@echo "Dependencies installed into $(VENV)."

## run: launch the game with the default configuration file
run:
	@$(VENV_PYTHON) $(ENTRY) $(CONFIG)

## debug: launch the game under the Python debugger (pdb)
debug:
	@$(VENV_PYTHON) -m pdb $(ENTRY) $(CONFIG)

## clean: remove caches and Python build artefacts
clean:
	@find . -not -path "./$(VENV)/*" -type d -name "__pycache__" -prune -exec rm -rf {} +
	@find . -not -path "./$(VENV)/*" -type f -name "*.py[cod]" -delete
	@rm -rf .mypy_cache .pytest_cache build dist *.egg-info
	@rm -rf dist
	@echo "Cleaned."

## lint: run flake8 and mypy with the flags required by the subject
lint:
	@$(VENV_PYTHON) -m flake8 .
	@$(VENV_PYTHON) -m mypy . $(MYPY_FLAGS)
	@echo "Lint passed."

## lint-strict: run flake8 and mypy in strict mode
lint-strict:
	@$(VENV_PYTHON) -m flake8 .
	@$(VENV_PYTHON) -m mypy . --strict
	@echo "Strict lint passed."

## test: run the unit test suite
test:
	@$(VENV_PYTHON) -m pytest tests -q

## help: list the available rules
help:
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## /  make /'