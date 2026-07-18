import importlib

import pytest

from riskaudit import SEED, __version__


def test_seed_is_frozen():
    assert SEED == 2026


def test_version_is_dev_prerelease():
    assert __version__ == "0.1.0.dev0"


@pytest.mark.parametrize("name", ["riskaudit.audit", "riskaudit.etl", "riskaudit.chile"])
def test_subpackage_imports(name):
    assert importlib.import_module(name) is not None
