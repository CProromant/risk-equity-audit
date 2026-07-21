import pandas as pd
from meps.etl.meps import _treated_ids


def test_treated_ids_flags_condition_or_psychotropic():
    cond = pd.DataFrame(
        {
            "DUPERSID": ["a", "b", "c"],
            "ICD10CDX": ["F32", "E11", "I10"],  # only a has a mental (F) code
            "CCSR1X": ["MBD005", "END001", "CIR007"],
        }
    )
    pmed = pd.DataFrame({"DUPERSID": ["d", "c"], "TC1": [249, 999]})  # d psychotropic, c not
    assert _treated_ids(cond, pmed) == {"a", "d"}
