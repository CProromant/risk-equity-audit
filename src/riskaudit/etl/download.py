from pathlib import Path

from riskaudit._config import RAW_DIR

PUF_IDS = ("h233", "h243", "h244", "h251")
URL_TEMPLATE = "https://meps.ahrq.gov/mepsweb/data_files/pufs/{id}/{id}dta.zip"


def download_meps(dest: Path = RAW_DIR) -> None:
    """Download and unzip the four MEPS PUFs, verifying against data/checksums.txt.

    A 404 means the URL pattern moved; stop and take the link from the PUF detail
    page rather than guessing (PROTOCOL §3.1, guardrail 1).
    """
    raise NotImplementedError
