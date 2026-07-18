import pandas as pd

from riskaudit._config import PROCESSED_DIR
from riskaudit.features import build_features
from riskaudit.models import train_all

if __name__ == "__main__":
    panel = pd.read_parquet(PROCESSED_DIR / "panel26.parquet")
    train_all(build_features(panel))
