import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "demo"))

from run_demo import main  # noqa: E402


def test_demo_runs_and_need_model_captures_more(tmp_path):
    out = main(out_html=tmp_path / "r.html", n=2000, seed=2026)
    html = Path(out).read_text(encoding="utf-8")
    assert "capture" in html and "data:image/png" in html
