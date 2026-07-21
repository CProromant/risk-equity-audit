# Windows: run these under Git Bash, or invoke the underlying scripts directly.
.PHONY: download etl models audit benchmark all test lint format validate-obermeyer

all: download etl models audit

download:
	python scripts/download_meps.py

etl:
	python scripts/build_panel.py

models:
	python scripts/train_models.py

audit:
	python scripts/run_audit.py

benchmark:
	python examples/benchmark/run_benchmark.py

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

validate-obermeyer:
	python -m validation.obermeyer_2019.reproduce
	RISKAUDIT_RUN_VALIDATION=1 python -m pytest -q tests/test_validation_obermeyer.py
