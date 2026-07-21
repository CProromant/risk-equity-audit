import pandas as pd
from meps.etl.meps import _clean


def _raw():
    # MEPS-plausible values with reserved missing codes (-1,-9,-15) mixed in.
    return pd.DataFrame(
        {
            "person_id": ["1", "2", "3", "4"],
            "stratum": [1001, 1001, 1002, 1002],
            "psu": [1, 2, 1, 2],
            "weight_long": [2300.0, 15000.0, 0.0, 367953.0],
            "age_t": [34, 71, -1, 58],
            "k6_t": [0, 24, -15, 8],
            "totexp_t1": [1234.5, 0.0, -1, 89000.0],
            "er_t": [0, 2, -9, 1],
        }
    )


def test_clean_maps_reserved_codes_to_nan():
    out = _clean(_raw())
    assert out["k6_t"].isna().sum() == 1
    assert out["age_t"].isna().sum() == 1
    assert out["totexp_t1"].isna().sum() == 1
    assert out["er_t"].isna().sum() == 1


def test_clean_keeps_design_and_valid_ranges():
    out = _clean(_raw())
    # A zero longitudinal weight is a real value, not a missing code.
    assert list(out["weight_long"]) == [2300.0, 15000.0, 0.0, 367953.0]
    assert out["stratum"].notna().all()
    assert out["k6_t"].dropna().between(0, 24).all()
    assert (out["totexp_t1"].dropna() >= 0).all()
