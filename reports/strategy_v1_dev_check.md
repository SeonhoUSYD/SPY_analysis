# Strategy v1: development-period accounting check

**Evaluation period:** 2008-01-07 to 2015-12-31. The first 252 sessions initialize the risk reference distribution. These results use the **same development sample used to design the rules** and do not establish out-of-sample performance.

| Cost (bp per traded dollar) | Strategy | Annualized return | Annualized volatility | Maximum drawdown | Rebalance events | ETF weight-change sum* | Accumulated costs / initial capital |
|---:|---|---:|---:|---:|---:|---:|---:|
| 0 | Strategy v1 | 7.4% | 10.7% | -19.6% | 181 | 99.4 | 0.000 |
| 0 | SPY buy-and-hold | 6.9% | 22.1% | -51.5% | 1 | 1.0 | 0.000 |
| 0 | Monthly equal weight | 6.5% | 10.0% | -20.1% | 96 | 4.3 | 0.000 |
| 5 | Strategy v1 | 6.7% | 10.7% | -19.9% | 181 | 99.4 | 0.074 |
| 5 | SPY buy-and-hold | 6.9% | 22.1% | -51.5% | 1 | 1.0 | 0.000 |
| 5 | Monthly equal weight | 6.5% | 10.0% | -20.1% | 96 | 4.3 | 0.003 |
| 20 | Strategy v1 | 4.8% | 10.7% | -20.7% | 181 | 99.4 | 0.274 |
| 20 | SPY buy-and-hold | 6.9% | 22.1% | -51.5% | 1 | 1.0 | 0.002 |
| 20 | Monthly equal weight | 6.4% | 10.0% | -20.2% | 96 | 4.3 | 0.011 |

*The weight-change sum aggregates absolute changes in ETF weights at each trade. A value of 1.0 is equivalent to buying ETF exposure equal to the entire portfolio once. It is not dollar turnover. Accumulated costs are actual modeled charges at each trade divided by initial capital, which is normalized to 1.

## Timing and accounting

- Friday risk decisions: low 173, medium 103, high 124.
- Friday close signals execute at the following session close. Adjusted-close execution is a research approximation.
- Cash accrues at the prior session's lagged three-month Treasury rate divided by 252.
- The strategies share evaluation dates and initial capital. Charges apply to traded ETF weight changes.
- A rebalance event can include multiple ETF purchases and sales; it is not a count of individual orders.

## Interpretation

Strategy v1 makes substantial allocation changes and is sensitive to transaction costs in this development sample. The next design question is whether fewer trades retain useful risk control. This table does not establish superiority. Data from 2016 onward are excluded from this calculation.

Any rule changes after seeing this table are development-stage fitting. Record revisions separately from `docs/strategy_v1.md` and keep the final test sample reserved.
