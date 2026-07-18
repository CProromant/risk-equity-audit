from pathlib import Path

from riskaudit._config import RAW_DIR


def build_panel26(raw_dir: Path = RAW_DIR, out_path: Path | None = None) -> Path:
    """Build panel26.parquet: one row per Panel 26 person, _t (2021) / _t1 (2022)."""
    raise NotImplementedError


def build_fyc_pooled(raw_dir: Path = RAW_DIR, out_path: Path | None = None) -> Path:
    """Build fyc_pooled.parquet: FYC 2021-2023 stacked with a year column."""
    raise NotImplementedError
