# Windows: run these under Git Bash, or invoke the underlying scripts directly.
.PHONY: download etl models audit chile demo all test lint format

all: download etl models audit

download:
	python scripts/download_meps.py

etl:
	python scripts/build_panel.py

models:
	python scripts/train_models.py

audit:
	python scripts/run_audit.py

chile:
	python scripts/build_chile.py

demo:
	python demo/run_demo.py

test:
	pytest

lint:
	ruff check .

format:
	ruff format .
