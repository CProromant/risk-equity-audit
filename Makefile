# Windows: run these under Git Bash, or invoke the underlying scripts directly.
.PHONY: download etl models audit figures benchmark all test lint format validate-obermeyer

all: download etl models audit

# The MEPS example lives under examples/meps (package `meps`); run it with examples/ on the path.
download:
	PYTHONPATH=examples python -m meps.scripts.download_meps

etl:
	PYTHONPATH=examples python -m meps.scripts.build_panel

models:
	PYTHONPATH=examples python -m meps.scripts.train_models

audit:
	PYTHONPATH=examples python -m meps.scripts.run_audit

figures:
	PYTHONPATH=examples python -m meps.make_figures

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
