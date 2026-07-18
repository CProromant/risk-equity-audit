import pandas as pd

from riskaudit._config import ARTIFACTS_DIR, PROCESSED_DIR


def main() -> None:
    dp = pd.read_parquet(PROCESSED_DIR / "panel26.parquet")
    k6_both = dp.k6_t.between(0, 24) & dp.k6_t1.between(0, 24)
    adult = dp.age_t >= 18
    severe = k6_both & (dp.k6_t >= 13)

    lines = [
        f"Panel 26 persons: {len(dp)}",
        f"Valid K6 both years: {int(k6_both.sum())}",
        f"Adults with K6 both years: {int((k6_both & adult).sum())}",
        f"Severe distress at t (K6>=13), K6 both years: {int(severe.sum())}",
        "",
        "Missingness (key vars):",
    ]
    lines += [
        f"  {c:16s} {dp[c].isna().mean():.1%}"
        for c in ("k6_t", "k6_t1", "totexp_t", "totexp_t1", "insurance_t", "poverty_t")
    ]
    lines += ["", "TOTEXP_t1 quantiles (unweighted):"]
    lines += [
        f"  p{int(q * 100)}: {v:,.0f}" for q, v in dp.totexp_t1.quantile([0.5, 0.9, 0.99]).items()
    ]

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    out = ARTIFACTS_DIR / "meps_profile.txt"
    out.write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
