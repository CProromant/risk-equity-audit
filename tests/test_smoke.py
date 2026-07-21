import importlib
from importlib.metadata import version

from riskaudit import SEED, __version__


def test_seed_is_frozen():
    assert SEED == 2026


def test_version_is_single_sourced():
    assert __version__ == version("riskaudit")


def test_audit_subpackage_imports():
    assert importlib.import_module("riskaudit.audit") is not None
