from pathlib import Path

import pandas as pd

from riskaudit._config import ARTIFACTS_DIR


def build_chile_figures(
    sources: dict[str, pd.DataFrame], out_dir: Path = ARTIFACTS_DIR
) -> list[Path]:
    """Render the four gap figures and the country table, each citing its source."""
    raise NotImplementedError
