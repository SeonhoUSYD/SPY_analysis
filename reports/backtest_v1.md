# Frozen strategy v1 backtest

| Period | Cost (bp) | Strategy | CAGR | Volatility | Max drawdown | Rebalances | Costs / initial capital |
|---|---:|---|---:|---:|---:|---:|---:|
| Development | 0 | Strategy v1 | 7.41% | 10.66% | -19.61% | 181 | 0.0000 |
| Development | 0 | SPY buy-and-hold | 6.95% | 22.14% | -51.48% | 1 | 0.0000 |
| Development | 0 | Monthly equal weight | 6.54% | 9.98% | -20.13% | 96 | 0.0000 |
| Development | 5 | Strategy v1 | 6.75% | 10.67% | -19.87% | 181 | 0.0742 |
| Development | 5 | SPY buy-and-hold | 6.94% | 22.14% | -51.48% | 1 | 0.0005 |
| Development | 5 | Monthly equal weight | 6.51% | 9.98% | -20.14% | 96 | 0.0027 |
| Development | 20 | Strategy v1 | 4.77% | 10.68% | -20.65% | 181 | 0.2736 |
| Development | 20 | SPY buy-and-hold | 6.92% | 22.14% | -51.48% | 1 | 0.0020 |
| Development | 20 | Monthly equal weight | 6.42% | 9.98% | -20.18% | 96 | 0.0108 |
| Validation | 0 | Strategy v1 | 15.42% | 6.62% | -3.38% | 62 | 0.0000 |
| Validation | 0 | SPY buy-and-hold | 17.65% | 10.35% | -9.19% | 1 | 0.0000 |
| Validation | 0 | Monthly equal weight | 10.98% | 6.67% | -9.80% | 24 | 0.0000 |
| Validation | 5 | Strategy v1 | 14.46% | 6.61% | -3.50% | 62 | 0.0199 |
| Validation | 5 | SPY buy-and-hold | 17.62% | 10.35% | -9.19% | 1 | 0.0005 |
| Validation | 5 | Monthly equal weight | 10.94% | 6.67% | -9.81% | 24 | 0.0007 |
| Validation | 20 | Strategy v1 | 11.62% | 6.61% | -3.85% | 62 | 0.0775 |
| Validation | 20 | SPY buy-and-hold | 17.53% | 10.35% | -9.22% | 1 | 0.0020 |
| Validation | 20 | Monthly equal weight | 10.82% | 6.67% | -9.82% | 24 | 0.0030 |
| Final test | 0 | Strategy v1 | 14.65% | 10.51% | -13.32% | 159 | 0.0000 |
| Final test | 0 | SPY buy-and-hold | 14.16% | 19.46% | -33.72% | 1 | 0.0000 |
| Final test | 0 | Monthly equal weight | 9.75% | 10.15% | -22.95% | 96 | 0.0000 |
| Final test | 5 | Strategy v1 | 14.00% | 10.51% | -13.32% | 159 | 0.0714 |
| Final test | 5 | SPY buy-and-hold | 14.15% | 19.46% | -33.72% | 1 | 0.0005 |
| Final test | 5 | Monthly equal weight | 9.72% | 10.15% | -22.96% | 96 | 0.0022 |
| Final test | 20 | Strategy v1 | 12.06% | 10.53% | -14.20% | 159 | 0.2638 |
| Final test | 20 | SPY buy-and-hold | 14.13% | 19.46% | -33.72% | 1 | 0.0020 |
| Final test | 20 | Monthly equal weight | 9.65% | 10.15% | -22.99% | 96 | 0.0087 |

## Final-test findings

At 5 bp per traded dollar, v1 returned 14.00% annualized versus 14.15% for SPY, with maximum drawdowns of -13.32% and -33.72%, respectively. V1 volatility was 10.51% versus 19.46% for SPY. At 20 bp, v1 annualized return fell to 12.06% versus 14.13% for SPY. These observations support a historical reduction in portfolio risk, not a claim of return superiority. The small return difference is sensitive to execution and data assumptions.

## Protocol and interpretation

- Strategy v1 allocation rules remained unchanged after validation and before the authorized final test; no parameter search was performed. Development: 2008-01-07 to 2015-12-31. Validation: the first trading session of 2016 through the last trading session of 2017. Final test: 2018-01-02 through 2025-12-31. The final test is now observed and cannot be reused as an unseen sample for later rule changes.
- Each period starts from capital of 1 in cash, with an initial strategy allocation executed at the first evaluation close using the preceding session's signal. Subsequent strategy decisions occur on trading Fridays and execute at the next session close. The initial allocation is a period-boundary exception to the Friday schedule. Holdings earn returns only after execution.
- Benchmarks start on the same close. Equal weight trades at the first session close of each new month. Prices are adjusted closes, so these are approximate total-return accounting prices, not executable quotes. Fractional holdings are allowed.
- Costs are charged on absolute dollars bought and sold, solving for post-cost target holdings. The initial purchase is charged; terminal liquidation is not charged. Scenarios of 0, 5 and 20 bp approximate aggregate trading friction; no separate spread or impact model is added.
- Cash earns the prior session's lagged DGS3MO annual rate divided by 252. This is a yield-based proxy, not a tradable cash instrument return. Additional management fees and taxes are not deducted; ETF fund expenses are already reflected in the price history.
- CAGR uses 252 trading sessions per year and the number of close-to-close intervals. Volatility excludes the initial purchase charge; portfolio value and drawdowns include it. Rebalances are events rather than individual orders.
- ETF prices come from the secondary mirror documented in data/raw/sources.json; VIX and rates come from FRED. Historical data revisions and adjusted-price execution limit realism. No claim of investor-executable results is made.
- Validation covers only two years. Any rule changes informed by this result consume that validation sample. Any changes informed by the final test require new future data or a separately justified evaluation design; relabeling the same dates does not restore an unseen test.

## Accounting checks

Historical wealth and holdings are identical when future observations are appended. Signal values are identical on truncated histories. Portfolio weights sum to one, portfolios remain positive, and no data after 2025-12-31 are loaded. Development and validation are computed from truncated histories, excluding subsequent periods. These checks address implementation timing and accounting, not profitability.
