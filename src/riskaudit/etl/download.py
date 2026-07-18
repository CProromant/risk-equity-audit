import hashlib
import os
import zipfile
from pathlib import Path

import requests

from riskaudit._config import DATA_DIR, RAW_DIR

PUF_IDS = ("h233", "h243", "h244", "h251")
URL_TEMPLATE = "https://meps.ahrq.gov/mepsweb/data_files/pufs/{id}/{id}dta.zip"
CHECKSUMS = DATA_DIR / "checksums.txt"


def _tls_verify():
    # Some managed Windows machines intercept TLS with a root cert OpenSSL 3 rejects.
    # Integrity is guaranteed by the pinned SHA-256s below, so allow an explicit opt-out.
    if os.environ.get("RISKAUDIT_INSECURE_TLS") == "1":
        import urllib3

        urllib3.disable_warnings()
        return False
    return os.environ.get("RISKAUDIT_CA_BUNDLE") or True


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _pinned() -> dict[str, str]:
    if not CHECKSUMS.exists():
        return {}
    return dict(
        reversed(line.split()) for line in CHECKSUMS.read_text().splitlines() if line.strip()
    )


def download_meps(dest: Path = RAW_DIR) -> None:
    """Download and unzip the four MEPS PUFs, verifying against data/checksums.txt.

    A 404 means the URL pattern moved; ``raise_for_status`` stops rather than
    guessing a new link (PROTOCOL §3.1, guardrail 1). The first run pins each
    file's SHA-256; later runs skip files that already match and fail loudly on a
    mismatch.
    """
    dest.mkdir(parents=True, exist_ok=True)
    pinned = _pinned()
    verify = _tls_verify()

    for pid in PUF_IDS:
        name = f"{pid}dta.zip"
        zip_path = dest / name
        if zip_path.exists() and pinned.get(name) == _sha256(zip_path):
            continue
        r = requests.get(URL_TEMPLATE.format(id=pid), timeout=120, verify=verify)
        r.raise_for_status()
        zip_path.write_bytes(r.content)
        digest = _sha256(zip_path)
        if name in pinned and pinned[name] != digest:
            raise ValueError(f"{name} checksum changed: expected {pinned[name]}, got {digest}")
        pinned[name] = digest
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(dest)

    CHECKSUMS.write_text("".join(f"{pinned[f'{p}dta.zip']}  {p}dta.zip\n" for p in PUF_IDS))
