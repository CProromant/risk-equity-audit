# MEPS 2021–2023 — a worked example on real survey data

An audit of cost-trained risk models on U.S. **MEPS** (AHRQ) microdata: the real-data
counterpart to the synthetic [`benchmark`](../benchmark) and the [`Obermeyer`](../../validation/obermeyer_2019)
reproduction. It exercises the full library — including the survey-design CIs and the
`incremental_lift` contribution metric — on messy, weighted, longitudinal data.

This is an **example, not the product**; the product is `riskaudit.audit`.

## Run it

The pipeline needs the heavy stack (`pip install -e ".[dev]"` from the repo root) and
downloads the MEPS PUFs on first run (free, no registration; pinned by SHA-256 in
`examples/meps/data/checksums.txt`). Each step runs the `meps` package with `examples/` on the path
(the `make` targets handle that):

```bash
make download   # fetch + checksum the PUFs into examples/meps/data/raw
make etl        # build panel26.parquet and the treatment proxy
make models     # three comparable LightGBM models (spend / avoidable-util / K6)
make audit      # the weighted, design-based audit -> examples/meps/artifacts/meps_audit.html
make figures    # regenerate the README figures from the audit
```

Behind a TLS-intercepting proxy, prefix the download with `RISKAUDIT_INSECURE_TLS=1`
(integrity still comes from the checksums). No microdata is versioned — everything under
`examples/meps/data` and `examples/meps/artifacts` is git-ignored.

## What it finds

On the Panel 26 analytic sample (~3,001 adults with valid K6 in both years), the
spend-trained model captures only ~15% of top-decile K6 need — barely above the ~10%
random floor, far below the ~41% oracle; a K6-trained model reaches ~29%. Among the
people the spend model deprioritizes, those in distress run up more *total* future cost
than it predicted (incremental lift +0.77 log-dollars with the mental-health features,
+1.05 without — both 95% CIs exclude zero): the bias is in the **label**, not missing
information.

**Honest limit:** that excess does **not** appear on non-psychiatric utilization (lift ≈ 0,
CI includes zero), so the non-psychiatric-spending mechanism is *not* demonstrated here.
The severe-untreated subgroup (n ≈ 40) is descriptive only. Full reasoning, definitions
and caveats are in [`METHODS.md`](METHODS.md).
