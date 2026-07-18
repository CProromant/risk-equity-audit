from riskaudit.chile.figures import build_chile_figures
from riskaudit.chile.parsers import load_chile_sources

if __name__ == "__main__":
    build_chile_figures(load_chile_sources())
