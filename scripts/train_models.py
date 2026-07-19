from riskaudit.etl.meps import load_panel
from riskaudit.features import build_features
from riskaudit.models import train_all

if __name__ == "__main__":
    train_all(build_features(load_panel()))
