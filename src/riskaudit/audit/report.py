from pathlib import Path
from typing import Any


def audit_report(results: dict[str, Any], out_html: str | Path) -> Path:
    """Render audit results into one self-contained HTML file.

    Takes the objects returned by the audit functions (keyed by name) and
    writes a single HTML document with every figure inlined as a data URI, so
    it opens with no external assets. Returns the written path.
    """
    raise NotImplementedError
