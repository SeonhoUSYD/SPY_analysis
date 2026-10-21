# Strategy v1: risk levels and defensive-asset eligibility

## Objective and rationale

Allocate across SPY (US equities), TLT (long-duration US Treasuries), GLD (gold), and cash. Use the risk level to set equity exposure, check recent asset behavior before assigning defensive capital, and skip small allocation changes.

The design begins with observations in the 2007-2015 development sample: higher month-end VIX was associated with higher subsequent SPY volatility; the strength of SPY/TLT correlation varied; and TLT and GLD reacted differently on severe SPY down days. These observations motivate experiments and do not establish return predictability or outperformance.

The numeric cutoffs below are initial experimental choices. They were not estimated as optimal weights from the charts. Record changes as a new strategy version and evaluate them only within development data before using validation results.

## Decisions and execution

1. Make decisions after the Friday ETF close. Skip weeks when Friday is not a trading session.
2. Use adjusted closes through the decision date and one-session-lagged VIX and Treasury-rate inputs.
3. Execute at the next trading session close. Adjusted-close execution is a research approximation rather than a historical executable quote.

## Allocation rules

- Compare one-session-lagged VIX with its trailing 252-session distribution. Below the 33rd percentile is low risk; above the 67th is high risk; the remainder is medium risk.
- Set target SPY exposure to 65% in low risk, 40% in medium risk, and 15% in high risk.
- TLT qualifies as a defensive candidate only if its trailing 63-session return is positive and its trailing 63-session daily-return correlation with SPY is below -0.15.
- GLD qualifies only if its trailing 63-session return is positive.
- Divide the remaining target weight equally among qualifying defensive candidates. If neither qualifies, hold the remaining allocation in cash.
- Skip a rebalance when the sum of absolute ETF-weight changes is less than 10 percentage points. Cash is excluded from this sum.

## Evaluation protocol

Use the same initial capital, dates, and execution assumptions for strategy v1, SPY buy-and-hold, and monthly equal-weight ETF rebalancing. Apply transaction costs to both ETF purchases and sales, with scenarios of 0, 5, and 20 basis points per traded dollar. Approximate cash accrual with the available lagged DGS3MO rate divided by 100 and 252.

Use 2007-2015 for development and accounting checks, 2016-2017 for validation, and reserve 2018-2025 for final out-of-sample evaluation. Report returns, volatility, drawdowns, rebalance events, weight changes, and accumulated charges together. A rebalance event can contain several individual ETF orders.

## Questions the experiment can answer

- Does actual equity exposure fall in high-risk states, allowing for execution delays and skipped trades?
- Do defensive eligibility checks materially change allocations?
- Does the no-trade rule reduce trading enough to improve net outcomes?
- Are outcomes robust to costs and later market conditions?

## Development finding

The initial development-only run produced substantial allocation changes and was sensitive to costs. This motivates testing whether a lower-trading variant retains risk control. It does not establish a successful investment strategy. See [the development check](../reports/strategy_v1_dev_check.md).

## Frozen validation run

The unchanged allocation rules were evaluated on 2016–2017 after the development accounting check. See [the full backtest protocol and results](../reports/backtest_v1.md). Each evaluation period resets capital, so its initial close allocation uses the preceding session signal as an explicitly documented boundary exception. Transaction charges are solved against post-cost target holdings. The 2018–2025 final test remains reserved.
