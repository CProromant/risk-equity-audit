from meps.etl.meps import _spec


def test_panel_standard_names_present_and_documented():
    p = _spec()["panel26"]
    names = {std for grp in ("design", "t", "t1") for std in p[grp]}
    assert {"person_id", "k6_t", "k6_t1", "totexp_t", "totexp_t1", "weight_long"} <= names
    for grp in ("design", "t", "t1"):
        for entry in p[grp].values():
            assert entry["name"] and entry["label"]


def test_fyc_suffix_and_sources():
    f = _spec()["fyc"]
    assert f["suffix"]["totexp"]["name"].format(yy="23") == "TOTEXP23"
    assert set(f["sources"]) == {2021, 2022, 2023}
