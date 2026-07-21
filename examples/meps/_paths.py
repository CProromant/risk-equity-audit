import os
from pathlib import Path

# The MEPS example keeps its data and artifacts self-contained under examples/meps;
# override with RISKAUDIT_MEPS_ROOT to point them elsewhere.
MEPS_ROOT = Path(os.environ.get("RISKAUDIT_MEPS_ROOT", Path(__file__).resolve().parent))
DATA_DIR = MEPS_ROOT / "data"
ARTIFACTS_DIR = MEPS_ROOT / "artifacts"

RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
