import os
from pathlib import Path

SEED = 2026

PROJECT_ROOT = Path(os.environ.get("RISKAUDIT_ROOT", Path.cwd()))
DATA_DIR = PROJECT_ROOT / "data"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CHILE_DIR = DATA_DIR / "chile"
SYNTHETIC_DIR = DATA_DIR / "synthetic"
