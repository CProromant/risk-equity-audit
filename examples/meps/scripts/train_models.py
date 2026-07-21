from meps.etl.meps import load_panel
from meps.features import build_features
from meps.models import train_all

if __name__ == "__main__":
    train_all(build_features(load_panel()))
