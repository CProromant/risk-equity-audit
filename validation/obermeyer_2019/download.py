import hashlib
import os
from pathlib import Path

import requests

URL = "https://gitlab.com/labsysmed/dissecting-bias/-/raw/master/data/data_new.csv"
SHA256 = "5341f90f3a1d330557620af1c734e552abe0ad57053055dd13dbccc6d8384d74"
DATA = Path(__file__).with_name("data") / "data_new.csv"


def _tls_verify():
    # Same TLS-interception escape hatch as the MEPS downloader; integrity is the
    # pinned SHA-256, not the transport.
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


def fetch(dest: Path = DATA) -> Path:
    """Download Obermeyer et al.'s public synthetic dataset (~18 MB), pinned by SHA-256.

    Git-ignored; a checksum mismatch stops rather than proceeding on changed data.
    """
    if dest.exists() and _sha256(dest) == SHA256:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(URL, timeout=180, verify=_tls_verify())
    r.raise_for_status()
    dest.write_bytes(r.content)
    got = _sha256(dest)
    if got != SHA256:
        raise ValueError(f"checksum mismatch: expected {SHA256}, got {got}")
    return dest


if __name__ == "__main__":
    print(fetch())
