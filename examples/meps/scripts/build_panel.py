from meps.etl.meps import build_fyc_pooled, build_panel26, build_treatment_proxy

if __name__ == "__main__":
    build_panel26()
    build_fyc_pooled()
    build_treatment_proxy()
