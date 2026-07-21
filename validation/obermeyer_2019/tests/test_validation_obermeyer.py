import os
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("RISKAUDIT_RUN_VALIDATION") != "1",
    reason="set RISKAUDIT_RUN_VALIDATION=1 to run the Obermeyer validation (downloads ~18 MB)",
)

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # repo root → validation package


def test_reproduces_obermeyer_direction():
    from validation.obermeyer_2019.reproduce import reproduce

    r = reproduce()
    # The score ranks by cost, not health, so it leaves need behind — between floor and oracle.
    assert r["floor"] < r["capture"] < r["oracle"]
    # The paper's disparity: less of Black patients' need is captured than White's.
    assert r["capture_black"] < r["capture_white"]
    # And Black patients admitted to the tier are sicker at the same priority level.
    assert r["illness_black"] > r["illness_white"]
    # Re-ranking by health raises the Black share of the tier, and reshuffles most of it.
    assert r["black_share_health"] > r["black_share_cost"]
    assert r["turnover"] > 0.5
