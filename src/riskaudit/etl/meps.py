from pathlib import Path

import pandas as pd
import pyreadstat
import yaml

from riskaudit._config import PROCESSED_DIR, RAW_DIR

_DICT = Path(__file__).with_name("dictionary.yml")

# MEPS reserved codes: -1 inapplicable, -7 refused, -8 don't know, -9 not
# ascertained, -15 cannot be computed. Turned into NaN everywhere except the
# design columns below, where a negative would be a real value we must keep.
_MISSING = [-1, -7, -8, -9, -15]
_KEEP_RAW = {
    "person_id",
    "panel",
    "stratum",
    "psu",
    "weight_long",
    "weight_saq_long",
    "weight_fy",
    "weight_saq",
    "year",
}


def _spec() -> dict:
    return yaml.safe_load(_DICT.read_text())


def _read(fid: str, names, raw_dir: Path) -> pd.DataFrame:
    df, _ = pyreadstat.read_dta(str(raw_dir / f"{fid}.dta"), usecols=list(names))
    return df


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in df.columns if c not in _KEEP_RAW]
    df[cols] = df[cols].mask(df[cols].isin(_MISSING))
    return df


def build_panel26(raw_dir: Path = RAW_DIR, out_path: Path | None = None) -> Path:
    """Build panel26.parquet: one row per Panel 26 person, _t (2021) / _t1 (2022)."""
    p = _spec()["panel26"]
    rename = {e["name"]: std for grp in ("design", "t", "t1") for std, e in p[grp].items()}
    df = _clean(_read("h244", rename, raw_dir).rename(columns=rename))
    out = out_path or PROCESSED_DIR / "panel26.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    return out


def build_fyc_pooled(raw_dir: Path = RAW_DIR, out_path: Path | None = None) -> Path:
    """Build fyc_pooled.parquet: FYC 2021-2023 stacked with a year column."""
    f = _spec()["fyc"]
    frames = []
    for year, fid in f["sources"].items():
        yy = str(year)[2:]
        rename = {e["name"]: std for std, e in f["fixed"].items()}
        rename |= {e["name"].format(yy=yy): std for std, e in f["suffix"].items()}
        df = _read(fid, rename, raw_dir).rename(columns=rename)
        df["year"] = int(year)
        frames.append(_clean(df))
    out = out_path or PROCESSED_DIR / "fyc_pooled.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(frames, ignore_index=True).to_parquet(out, index=False)
    return out
