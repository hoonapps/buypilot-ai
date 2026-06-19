.PHONY: install lint test verify run docker-build

install:
	python3 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -e '.[dev]'

lint:
	.venv/bin/ruff check .

test:
	.venv/bin/python -m pytest -q

verify: lint test

run:
	.venv/bin/uvicorn specpilot_ai.api.main:app --reload

docker-build:
	docker build -t specpilot-ai:local .
