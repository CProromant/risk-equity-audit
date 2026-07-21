import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples" / "benchmark"))

from run_benchmark import main  # noqa: E402


def test_benchmark_recovers_the_planted_bias(tmp_path):
    out, s = main(out_html=tmp_path / "r.html", n=3000, seed=2026, n_boot=100)
    html = Path(out).read_text(encoding="utf-8")
    assert "capture" in html and "data:image/png" in html and "<table" in html

    # Planted: the cost score captures less need than ranking by need itself,
    cap = s["by_group"]
    assert s["cap_cost"].value < s["cap_need"].value
    # the underserved subgroup is captured worse than the served one,
    assert cap.loc["underserved", "capture"] < cap.loc["served", "capture"]
    # and relabeling toward need raises the underserved share of the top-k.
    fr = s["frontier"]
    assert fr.loc[0.0, "share_underserved"] > fr.loc[1.0, "share_underserved"]
