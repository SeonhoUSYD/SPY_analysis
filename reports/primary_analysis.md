# Initial analysis: the case for risk-dependent ETF allocation

## Research question and scope

Do changing risk levels and asset relationships justify testing a VIX-informed allocation across SPY, TLT, GLD, and cash?

The development sample covers **2007-01-03 to 2015-12-31, 2,266 sessions**. Data from 2016 onward are reserved for validation and testing. These descriptive results do not establish strategy outperformance.

## Data and methods

- ETF prices: [pinned public adjusted-close mirror](https://github.com/manisahni/marketdata/tree/65a079329e379e104495f459e12e76a8f995585a). The publisher describes the file as a Yahoo Finance `auto_adjust=True` cache. It is a secondary mirror. Original files and SHA-256 hashes are stored locally. Adjusted closes are return-analysis proxies, not executable historical quotes.
- VIX: [FRED VIXCLS](https://fred.stlouisfed.org/series/VIXCLS). Cash-rate proxy: [FRED DGS3MO](https://fred.stlouisfed.org/series/DGS3MO). Model inputs use values lagged by at least one trading session.
- Spot checks: GLD closed at $396.31 on 2025-12-31 in the [Nasdaq history endpoint](https://api.nasdaq.com/api/quote/GLD/historical?assetclass=etf&limit=3&fromdate=2025-01-01&todate=2025-12-31); the dataset matches to rounding. FRED VIX is 82.69 on 2020-03-16. These two checks do not validate the entire history and are not development-period performance analysis.
- Daily simple return: adjusted close(t) / adjusted close(t-1) - 1. Correlations use contemporaneous daily returns.
- For VIX analysis, one-session-lagged VIX at each month-end is paired with the sample standard deviation of the next 20 SPY returns, annualized by the square root of 252. Some forward windows can overlap. No independence-based significance test is reported.

## Observation 1: diversification relationships vary

Full-development-sample correlations are **-0.45** for SPY/TLT and **+0.06** for SPY/GLD.

| Period | Return observations | SPY / TLT | SPY / GLD |
|---|---:|---:|---:|
| 2007~2009 | 755 | -0.41 | +0.06 |
| 2010~2012 | 754 | -0.65 | +0.10 |
| 2013~2015 | 756 | -0.35 | +0.00 |

The 126-session rolling SPY/TLT correlation was positive on **1.5%** of eligible sessions. It was predominantly negative in this sample, but its strength varied. This supports testing a current relationship filter without proving that dynamic allocation will improve returns.

![Rolling return correlation](figures/initial_correlation.png)

## Observation 2: defensive assets behave differently on stress days

The fifth-percentile SPY daily-return threshold is **-2.05%**, identifying **114 days**. Average same-day returns were SPY **-3.31%**, TLT **1.22%**, and GLD **-0.17%**. TLT was positive on **86.0%** of those days; GLD on **44.7%**.

The averages and distributions motivate checking defensive candidates individually. Stress dates were selected retrospectively; they are not signals that could have been known in advance.

![Stress-day return distributions](figures/initial_stress.png)

## Observation 3: VIX and subsequent risk are associated

The lower and upper quartile cutoffs for lagged month-end VIX are **14.68** and **24.34**. Median subsequent 20-session annualized SPY volatility is **10.2%** (n=27) in the low-VIX group and **20.7%** (n=27) in the high-VIX group, a ratio of **2.02**.

This supports testing VIX as a risk input. It does not establish return-direction predictability or a causal effect.

![VIX and subsequent volatility](figures/initial_vix_forward.png)

## Experiment decisions

1. Compare SPY buy-and-hold, monthly equal-weight rebalancing, and rule strategy v1 on the same backtester.
2. Check risk-dependent equity exposure, defensive-asset eligibility, and the no-trade rule separately.
3. Report allocation, transaction count, turnover, costs, returns, and maximum drawdown together.
4. Generate signals from information available at the decision time and execute no earlier than the following session. Reusing held-out results to redesign the strategy would contaminate that evaluation.

## Limitations and viewing

The ETF mirror needs broader independent cross-checks before final strategy evaluation. The development window includes the financial crisis, and its relationships may not persist. VIX is an implied-risk measure; DGS3MO is a cash-return proxy. These plots contain asset observations, not a backtested trading policy. The separate strategy report is an in-sample prototype check.

Open `reports/initial_analysis.html` for interactive charts or `notebooks/initial_analysis.ipynb` for saved chart outputs. Rebuild visual assets with `.venv/bin/python scripts/build_initial_analysis.py`.
