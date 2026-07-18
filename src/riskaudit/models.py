from pathlib import Path

from riskaudit._config import ARTIFACTS_DIR, SEED
from riskaudit.features import FeatureMatrix


def train_all(features: FeatureMatrix, out_dir: Path = ARTIFACTS_DIR, seed: int = SEED) -> Path:
    """Train the three same-class models and persist models, OOF/test preds, metrics."""
    raise NotImplementedError
