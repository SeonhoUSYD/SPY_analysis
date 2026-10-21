"""Descriptive, development-period analysis that motivates the strategy design."""

from __future__ import annotations

import csv
import math
import statistics as stats
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "market_daily.csv"
REPORT = ROOT / "reports" / "primary_analysis.md"
FIGURES = ROOT / "reports" / "figures"
END_DEV = "2015-12-31"
SYMBOLS = ("spy", "tlt", "gld")


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * p
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def corr(xs: list[float], ys: list[float]) -> float:
    x_mean, y_mean = stats.mean(xs), stats.mean(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    denominator = math.sqrt(
        sum((x - x_mean) ** 2 for x in xs)
        * sum((y - y_mean) ** 2 for y in ys)
    )
    return numerator / denominator


def pct(x: float, digits: int = 1) -> str:
    return f"{100 * x:.{digits}f}%"


def svg_line(values: list[tuple[str, float]], title: str, path: Path) -> None:
    width, height = 920, 300
    left, right, top, bottom = 70, 25, 48, 46
    plot_w, plot_h = width - left - right, height - top - bottom
    y_min, y_max = -1.0, 1.0
    points = []
    for idx, (_, value) in enumerate(values):
        x = left + (idx / max(1, len(values) - 1)) * plot_w
        y = top + (y_max - value) / (y_max - y_min) * plot_h
        points.append(f"{x:.1f},{y:.1f}")
    y_zero = top + plot_h / 2
    year_labels = []
    for year in range(2008, 2016, 2):
        positions = [i for i, (day, _) in enumerate(values) if day.startswith(str(year))]
        if positions:
            x = left + positions[0] / max(1, len(values) - 1) * plot_w
            year_labels.append(f'<text x="{x:.1f}" y="{height-17}" text-anchor="middle">{year}</text>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="#ffffff"/>
<text x="{left}" y="27" font-family="Arial,sans-serif" font-size="17" font-weight="bold" fill="#17233b">{title}</text>
<g font-family="Arial,sans-serif" font-size="12" fill="#56637a">
<text x="{left-12}" y="{top+4}" text-anchor="end">+1</text>
<text x="{left-12}" y="{y_zero+4:.1f}" text-anchor="end">0</text>
<text x="{left-12}" y="{top+plot_h+4}" text-anchor="end">-1</text>
{''.join(year_labels)}</g>
<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" stroke="#8b96a9"/>
<line x1="{left}" y1="{y_zero:.1f}" x2="{width-right}" y2="{y_zero:.1f}" stroke="#c7d0de" stroke-dasharray="4 4"/>
<polyline fill="none" stroke="#1766a3" stroke-width="1.5" points="{' '.join(points)}"/>
</svg>'''
    path.write_text(svg, encoding="utf-8")


def svg_bars(low: float, high: float, n_low: int, n_high: int, path: Path) -> None:
    width, height = 690, 320
    top, bottom = 58, 58
    maximum = max(low, high) * 1.25
    baseline = height - bottom
    bars = []
    for x, value, label, n, color in (
        (170, low, "Bottom VIX quartile", n_low, "#56a3a6"),
        (390, high, "Top VIX quartile", n_high, "#c05c52"),
    ):
        bar_h = value / maximum * (baseline - top)
        bars.append(f'''<rect x="{x}" y="{baseline-bar_h:.1f}" width="130" height="{bar_h:.1f}" fill="{color}"/>
<text x="{x+65}" y="{baseline-bar_h-12:.1f}" text-anchor="middle" font-weight="bold">{value:.1f}%</text>
<text x="{x+65}" y="{baseline+22}" text-anchor="middle">{label}</text>
<text x="{x+65}" y="{baseline+40}" text-anchor="middle">n={n} month-ends</text>''')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="#ffffff"/>
<g font-family="Arial,sans-serif" fill="#17233b">
<text x="45" y="31" font-size="17" font-weight="bold">Median forward SPY volatility by VIX quartile</text>
{''.join(bars)}</g><line x1="65" y1="{baseline}" x2="625" y2="{baseline}" stroke="#8b96a9"/>
</svg>'''
    path.write_text(svg, encoding="utf-8")


def main() -> None:
    with DATA.open(newline="", encoding="utf-8") as stream:
        all_rows = list(csv.DictReader(stream))
    rows = [row for row in all_rows if row["date"] <= END_DEV]
    if len(rows) < 2000 or any(row["date"] > END_DEV for row in rows):
        raise ValueError("Development-period isolation failed")

    returns: list[dict[str, float | str]] = []
    for idx in range(1, len(rows)):
        item: dict[str, float | str] = {"date": rows[idx]["date"]}
        for symbol in SYMBOLS:
            key = f"{symbol}_adj_close"
            item[symbol] = float(rows[idx][key]) / float(rows[idx - 1][key]) - 1
        returns.append(item)

    spy = [float(row["spy"]) for row in returns]
    tlt = [float(row["tlt"]) for row in returns]
    gld = [float(row["gld"]) for row in returns]
    overall_corr = {"tlt": corr(spy, tlt), "gld": corr(spy, gld)}
    blocks = []
    for start, end in ((2007, 2009), (2010, 2012), (2013, 2015)):
        group = [row for row in returns if start <= int(str(row["date"])[:4]) <= end]
        blocks.append((f"{start}~{end}", len(group),
                       corr([float(r["spy"]) for r in group], [float(r["tlt"]) for r in group]),
                       corr([float(r["spy"]) for r in group], [float(r["gld"]) for r in group])))

    rolling = []
    for idx in range(125, len(returns)):
        rolling.append((str(returns[idx]["date"]), corr(spy[idx-125:idx+1], tlt[idx-125:idx+1])))
    positive_frac = sum(value > 0 for _, value in rolling) / len(rolling)

    threshold = percentile(spy, 0.05)
    stressed = [row for row in returns if float(row["spy"]) <= threshold]
    stress_mean = {s: stats.mean(float(row[s]) for row in stressed) for s in SYMBOLS}
    stress_positive = {s: sum(float(row[s]) > 0 for row in stressed) / len(stressed) for s in ("tlt", "gld")}

    monthly = []
    for idx in range(len(rows) - 21):
        if rows[idx]["date"][:7] == rows[idx + 1]["date"][:7]:
            continue
        if not rows[idx]["vix_lag1"]:
            continue
        future = [float(returns[j]["spy"]) for j in range(idx, idx + 20)]
        monthly.append((rows[idx]["date"], float(rows[idx]["vix_lag1"]), stats.stdev(future) * math.sqrt(252) * 100))
    vix_25 = percentile([r[1] for r in monthly], 0.25)
    vix_75 = percentile([r[1] for r in monthly], 0.75)
    low = [r[2] for r in monthly if r[1] <= vix_25]
    high = [r[2] for r in monthly if r[1] >= vix_75]
    low_median, high_median = stats.median(low), stats.median(high)

    FIGURES.mkdir(parents=True, exist_ok=True)
    svg_line(rolling, "SPY / TLT rolling 126-session correlation (2007-2015)", FIGURES / "rolling_spy_tlt_correlation.svg")
    svg_bars(low_median, high_median, len(low), len(high), FIGURES / "vix_future_volatility.svg")

    block_lines = "\n".join(
        f"| {label} | {n:,} | {c_tlt:+.2f} | {c_gld:+.2f} |"
        for label, n, c_tlt, c_gld in blocks
    )
    report = f"""# Initial analysis: the case for risk-dependent ETF allocation

## Research question and scope

Do changing risk levels and asset relationships justify testing a VIX-informed allocation across SPY, TLT, GLD, and cash?

The development sample covers **{rows[0]['date']} to {rows[-1]['date']}, {len(rows):,} sessions**. Data from 2016 onward are excluded from these initial calculations. The completed validation and final test are documented in the final report. These descriptive results do not establish strategy outperformance.

## Data and methods

- ETF prices: [pinned public adjusted-close mirror](https://github.com/manisahni/marketdata/tree/65a079329e379e104495f459e12e76a8f995585a). The publisher describes the file as a Yahoo Finance `auto_adjust=True` cache. It is a secondary mirror. Original files and SHA-256 hashes are stored locally. Adjusted closes are return-analysis proxies, not executable historical quotes.
- VIX: [FRED VIXCLS](https://fred.stlouisfed.org/series/VIXCLS). Cash-rate proxy: [FRED DGS3MO](https://fred.stlouisfed.org/series/DGS3MO). Model inputs use values lagged by at least one trading session.
- Spot checks: GLD closed at $396.31 on 2025-12-31 in the [Nasdaq history endpoint](https://api.nasdaq.com/api/quote/GLD/historical?assetclass=etf&limit=3&fromdate=2025-01-01&todate=2025-12-31); the dataset matches to rounding. FRED VIX is 82.69 on 2020-03-16. These two checks do not validate the entire history and are not development-period performance analysis.
- Daily simple return: adjusted close(t) / adjusted close(t-1) - 1. Correlations use contemporaneous daily returns.
- For VIX analysis, one-session-lagged VIX at each month-end is paired with the sample standard deviation of the next 20 SPY returns, annualized by the square root of 252. Some forward windows can overlap. No independence-based significance test is reported.

## Observation 1: diversification relationships vary

Full-development-sample correlations are **{overall_corr['tlt']:+.2f}** for SPY/TLT and **{overall_corr['gld']:+.2f}** for SPY/GLD.

| Period | Return observations | SPY / TLT | SPY / GLD |
|---|---:|---:|---:|
{block_lines}

The 126-session rolling SPY/TLT correlation was positive on **{pct(positive_frac)}** of eligible sessions. It was predominantly negative in this sample, but its strength varied. This supports testing a current relationship filter without proving that dynamic allocation will improve returns.

![Rolling return correlation](figures/initial_correlation.png)

## Observation 2: defensive assets behave differently on stress days

The fifth-percentile SPY daily-return threshold is **{pct(threshold, 2)}**, identifying **{len(stressed)} days**. Average same-day returns were SPY **{pct(stress_mean['spy'], 2)}**, TLT **{pct(stress_mean['tlt'], 2)}**, and GLD **{pct(stress_mean['gld'], 2)}**. TLT was positive on **{pct(stress_positive['tlt'])}** of those days; GLD on **{pct(stress_positive['gld'])}**.

The averages and distributions motivate checking defensive candidates individually. Stress dates were selected retrospectively; they are not signals that could have been known in advance.

![Stress-day return distributions](figures/initial_stress.png)

## Observation 3: VIX and subsequent risk are associated

The lower and upper quartile cutoffs for lagged month-end VIX are **{vix_25:.2f}** and **{vix_75:.2f}**. Median subsequent 20-session annualized SPY volatility is **{low_median:.1f}%** (n={len(low)}) in the low-VIX group and **{high_median:.1f}%** (n={len(high)}) in the high-VIX group, a ratio of **{high_median/low_median:.2f}**.

This supports testing VIX as a risk input. It does not establish return-direction predictability or a causal effect.

![VIX and subsequent volatility](figures/initial_vix_forward.png)

## Experiment decisions

1. Compare SPY buy-and-hold, monthly equal-weight rebalancing, and rule strategy v1 on the same backtester.
2. Check risk-dependent equity exposure, defensive-asset eligibility, and the no-trade rule separately.
3. Report allocation, transaction count, turnover, costs, returns, and maximum drawdown together.
4. Generate signals from information available at the decision time and execute no earlier than the following session. Reusing held-out results to redesign the strategy would contaminate that evaluation.

## Limitations and viewing

Broader independent cross-checking of the ETF mirror remains incomplete; the completed strategy results are conditional on this data source. The development window includes the financial crisis, and its relationships may not persist. VIX is an implied-risk measure; DGS3MO is a cash-return proxy. These plots contain asset observations, not a backtested trading policy. See final_report.md for the completed study and its review limitations.

Open `reports/initial_analysis.html` for interactive charts or `notebooks/initial_analysis.ipynb` for saved chart outputs. Rebuild visual assets with `.venv/bin/python scripts/build_initial_analysis.py`.
"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")
    print(f"development_days={len(rows)} stress_days={len(stressed)}")
    print(f"corr_spy_tlt={overall_corr['tlt']:.3f} corr_spy_gld={overall_corr['gld']:.3f}")
    print(f"vix_future_vol_low={low_median:.2f} high={high_median:.2f}")
    print(f"report={REPORT}")


if __name__ == "__main__":
    main()
