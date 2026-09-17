.PHONY: install test lint collect

install:
	python -m pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check src tests

collect:
	g1-scraper --term lgpd --max-pages 5 --page-size 10 --delay 1

