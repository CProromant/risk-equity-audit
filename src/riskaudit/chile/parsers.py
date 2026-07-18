from pathlib import Path

import pandas as pd

from riskaudit._config import CHILE_DIR


def load_chile_sources(src_dir: Path = CHILE_DIR) -> dict[str, pd.DataFrame]:
    """Parse the Chilean aggregate sources into tidy frames, one source per key.

    Tolerant parsers: where a MINSAL/SUSESO file is a fragile Excel/PDF, prefer a
    documented manual download over aggressive scraping (guardrail 6).
    """
    raise NotImplementedError
