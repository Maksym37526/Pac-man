.PHONY: install run debug clean lint lint-strict


install:
	uv venv .venv
	uv sync

run:
	uv run python pacman.py