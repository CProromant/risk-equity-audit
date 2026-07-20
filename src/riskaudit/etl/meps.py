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

# Multum therapeutic classes counted as psychotropic, verified against HC-229A value
# labels: antidepressants, antipsychotics, anxiolytics/sedatives/hypnotics, antimanic,
# ADHD agents, psychotherapeutics. Broad CNS catch-alls (57, 80) are excluded.
_MH_TC1 = frozenset(
    {67, 70, 71, 76, 77, 79, 208, 209, 210, 242, 249, 251, 306, 307, 308, 341, 504, 516}
)


def _spec() -> dict:
    return yaml.safe_load(_DICT.read_text())


def _read(fid: str, names, raw_dir: Path) -> pd.DataFrame:
    df, _ = pyreadstat.read_dta(str(raw_dir / f"{fid}.dta"), usecols=list(names))
    return df


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
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


def _treated_ids(cond: pd.DataFrame, pmed: pd.DataFrame) -> set:
    icd = cond["ICD10CDX"].astype(str)
    ccsr = cond["CCSR1X"].astype(str)
    ids = set(cond.loc[icd.str.startswith("F") | ccsr.str.startswith("MBD"), "DUPERSID"])
    return ids | set(pmed.loc[pmed["TC1"].isin(_MH_TC1), "DUPERSID"])


def build_treatment_proxy(raw_dir: Path = RAW_DIR, out_path: Path | None = None) -> Path:
    """Person-level 2021 mental-health treatment flag (docs/methods.md §1).

    Treated = a mental-health condition (ICD-10 F* or CCSR MBD*) in HC-231, or a
    psychotropic prescription (Multum class in ``_MH_TC1``) in HC-229A.
    """
    cond, _ = pyreadstat.read_dta(
        str(raw_dir / "h231.dta"), usecols=["DUPERSID", "ICD10CDX", "CCSR1X"]
    )
    pmed, _ = pyreadstat.read_dta(str(raw_dir / "h229a.dta"), usecols=["DUPERSID", "TC1"])
    ids = _treated_ids(cond, pmed)
    out = out_path or PROCESSED_DIR / "treatment.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"person_id": sorted(ids), "treated_mh": 1}).to_parquet(out, index=False)
    return out


def load_panel(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """panel26 with the person-level mental-health treatment flag merged in."""
    panel = pd.read_parquet(processed_dir / "panel26.parquet")
    treat = pd.read_parquet(processed_dir / "treatment.parquet")
    return panel.merge(treat, on="person_id", how="left").fillna({"treated_mh": 0})
