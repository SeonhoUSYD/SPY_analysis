"""Development-only accounting check for the predeclared strategy v1."""

from __future__ import annotations

import csv
import math
import statistics as stats
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "market_daily.csv"
OUTPUT = ROOT / "reports" / "strategy_v1_dev_check.md"
END_DEV = "2015-12-31"
ASSETS = ("spy", "tlt", "gld")


def percentile(values: list[float], p: float) -> float:
    values = sorted(values)
    x = (len(values) - 1) * p
    a = int(x)
    b = min(a + 1, len(values) - 1)
    return values[a] + (values[b] - values[a]) * (x - a)


def correlation(xs: list[float], ys: list[float]) -> float:
    xbar, ybar = stats.mean(xs), stats.mean(ys)
    numerator = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys))
    denominator = math.sqrt(sum((x - xbar) ** 2 for x in xs) * sum((y - ybar) ** 2 for y in ys))
    return numerator / denominator


def load(end: str = END_DEV) -> list[dict]:
    rows = []
    with DATA.open(newline="", encoding="utf-8") as stream:
        for raw in csv.DictReader(stream):
            if raw["date"] > end:
                break
            row = {"date": raw["date"], "day": date.fromisoformat(raw["date"])}
            for asset in ASSETS:
                row[asset] = float(raw[f"{asset}_adj_close"])
            row["vix"] = float(raw["vix_lag1"]) if raw["vix_lag1"] else None
            row["cash_rate"] = float(raw["dgs3mo_lag1"]) / 100 / 252 if raw["dgs3mo_lag1"] else 0.0
            rows.append(row)
    return rows


def signal(rows: list[dict], t: int) -> tuple[list[float], str, tuple[bool, bool]]:
    history = [row["vix"] for row in rows[t-251:t+1]]
    if any(value is None for value in history):
        raise ValueError("Missing VIX in signal history")
    low, high = percentile(history, .33), percentile(history, .67)
    current = rows[t]["vix"]
    if current < low:
        spy_weight, regime = .65, "low"
    elif current > high:
        spy_weight, regime = .15, "high"
    else:
        spy_weight, regime = .40, "mid"

    spy_returns = [rows[j]["spy"] / rows[j-1]["spy"] - 1 for j in range(t-62, t+1)]
    tlt_returns = [rows[j]["tlt"] / rows[j-1]["tlt"] - 1 for j in range(t-62, t+1)]
    tlt_ok = (
        correlation(spy_returns, tlt_returns) < -.15
        and rows[t]["tlt"] / rows[t-63]["tlt"] - 1 > 0
    )
    gld_ok = rows[t]["gld"] / rows[t-63]["gld"] - 1 > 0
    defensive = 1 - spy_weight
    candidates = int(tlt_ok) + int(gld_ok)
    tlt_weight = defensive / candidates if tlt_ok else 0.0
    gld_weight = defensive / candidates if gld_ok else 0.0
    cash_weight = 1 - spy_weight - tlt_weight - gld_weight
    target = [spy_weight, tlt_weight, gld_weight, cash_weight]
    assert abs(sum(target) - 1) < 1e-10 and min(target) >= -1e-10
    return target, regime, (tlt_ok, gld_ok)


def run(rows: list[dict], start: int, mode: str, cost_rate: float) -> dict:
    value = 1.0
    weights = [0.0, 0.0, 0.0, 1.0]
    values = []
    weight_history = []
    pnl_history = []
    cost_history = []
    trades = 0
    turnover = 0.0
    total_cost = 0.0
    decisions = {"low": 0, "mid": 0, "high": 0}
    pending = signal(rows, start - 1)[0] if mode in ("v1", "dynamic_cash") else None
    if mode == "dynamic_cash":
        pending = [pending[0], 0.0, 0.0, 1 - pending[0]]

    def rebalance(target: list[float]) -> None:
        nonlocal value, weights, trades, turnover, total_cost
        changed = sum(abs(target[i] - weights[i]) for i in range(3))
        if changed < 1e-12:
            return
        # Solve costs against post-cost target holdings rather than pre-cost weights.
        before = value
        after = before
        for _ in range(30):
            traded = sum(abs(after * target[i] - before * weights[i]) for i in range(3))
            after = before - traded * cost_rate
        charge = before - after
        value = after
        if value <= 0:
            raise ValueError("Transaction costs exhausted the portfolio")
        weights = target[:]
        trades += 1
        turnover += changed
        total_cost += charge

    for t in range(start, len(rows)):
        daily_pnl = [0.0] * 4
        costs_before = total_cost
        if t > start:
            relatives = [rows[t][a] / rows[t-1][a] for a in ASSETS]
            relatives.append(1 + rows[t-1]["cash_rate"])
            daily_pnl = [value * weights[i] * (relatives[i] - 1) for i in range(4)]
            components = [weights[i] * relatives[i] for i in range(4)]
            growth = sum(components)
            value *= growth
            weights = [component / growth for component in components]
        if mode in ("v1", "dynamic_cash"):
            if pending is not None:
                rebalance(pending)
                pending = None
            if rows[t]["day"].weekday() == 4 and t < len(rows) - 1:
                target, regime, _ = signal(rows, t)
                if mode == "dynamic_cash":
                    target = [target[0], 0.0, 0.0, 1 - target[0]]
                decisions[regime] += 1
                if sum(abs(target[i] - weights[i]) for i in range(3)) >= .10:
                    pending = target
        elif mode == "fixed40" and (t == start or rows[t]["date"][:7] != rows[t-1]["date"][:7]):
            rebalance([.4, 0.0, 0.0, .6])
        elif mode == "spy" and t == start:
            rebalance([1.0, 0.0, 0.0, 0.0])
        elif mode == "equal" and (t == start or rows[t]["date"][:7] != rows[t-1]["date"][:7]):
            rebalance([1/3, 1/3, 1/3, 0.0])
        values.append(value)
        weight_history.append(weights[:])
        pnl_history.append(daily_pnl)
        cost_history.append(total_cost - costs_before)
        assert abs(sum(weights) - 1) < 1e-8 and value > 0

    daily = [values[i] / values[i-1] - 1 for i in range(1, len(values))]
    high_water = 1.0
    worst_drawdown = 0.0
    for wealth in values:
        high_water = max(high_water, wealth)
        worst_drawdown = min(worst_drawdown, wealth / high_water - 1)
    return {
        "pnl": pnl_history,
        "costs": cost_history,
        "values": values,
        "weights": weight_history,
        "final": values[-1],
        "cagr": values[-1] ** (252 / max(1, len(values) - 1)) - 1,
        "volatility": stats.stdev(daily) * math.sqrt(252),
        "max_drawdown": worst_drawdown,
        "trades": trades,
        "turnover": turnover,
        "cost_fraction_initial": total_cost,
        "decisions": decisions,
        "dates": (rows[start]["date"], rows[-1]["date"]),
    }


def main() -> None:
    rows = load()
    first_friday = next(i for i in range(252, len(rows)-1) if rows[i]["day"].weekday() == 4)
    start = first_friday + 1
    lines = []
    for bps in (0, 5, 20):
        rate = bps / 10000
        for name, mode in (("Strategy v1", "v1"), ("SPY buy-and-hold", "spy"), ("Monthly equal weight", "equal")):
            result = run(rows, start, mode, rate)
            lines.append(
                f"| {bps} | {name} | {result['cagr']:.1%} | {result['volatility']:.1%} | "
                f"{result['max_drawdown']:.1%} | {result['trades']} | {result['turnover']:.1f} | "
                f"{result['cost_fraction_initial']:.3f} |"
            )
            if bps == 5 and mode == "v1":
                checked = result
    report = f"""# Strategy v1: development-period accounting check

**Evaluation period:** {checked['dates'][0]} to {checked['dates'][1]}. The first 252 sessions initialize the risk reference distribution. These results use the **same development sample used to design the rules** and do not establish out-of-sample performance.

| Cost (bp per traded dollar) | Strategy | Annualized return | Annualized volatility | Maximum drawdown | Rebalance events | ETF weight-change sum* | Accumulated costs / initial capital |
|---:|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(lines)}

*The weight-change sum aggregates absolute changes in ETF weights at each trade. A value of 1.0 is equivalent to buying ETF exposure equal to the entire portfolio once. It is not dollar turnover. Accumulated costs are actual modeled charges at each trade divided by initial capital, which is normalized to 1.

## Timing and accounting

- Friday risk decisions: low {checked['decisions']['low']}, medium {checked['decisions']['mid']}, high {checked['decisions']['high']}.
- Friday close signals execute at the following session close. Adjusted-close execution is a research approximation.
- Cash accrues at the prior session's lagged three-month Treasury rate divided by 252.
- The strategies share evaluation dates and initial capital. Charges apply to traded ETF weight changes.
- A rebalance event can include multiple ETF purchases and sales; it is not a count of individual orders.

## Interpretation

Strategy v1 makes substantial allocation changes and is sensitive to transaction costs in this development sample. The next design question is whether fewer trades retain useful risk control. This table does not establish superiority. Data from 2016 onward are excluded from this calculation.

Any rule changes after seeing this table are development-stage fitting. Record revisions separately from `docs/strategy_v1.md` and keep the final test sample reserved.
"""
    OUTPUT.write_text(report, encoding="utf-8")
    print(f"start={checked['dates'][0]} end={checked['dates'][1]}")
    print(f"v1_5bp_cagr={checked['cagr']:.4f} trades={checked['trades']}")
    print(f"report={OUTPUT}")


if __name__ == "__main__":
    main()
