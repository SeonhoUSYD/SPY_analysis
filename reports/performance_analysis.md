# Performance attribution and simple benchmarks

| Strategy | CAGR | Volatility | Max drawdown | Mean SPY weight | Rebalances |
|---|---:|---:|---:|---:|---:|
| Strategy v1 | 14.00% | 10.51% | -13.32% | 40.14% | 159 |
| SPY buy-and-hold | 14.15% | 19.46% | -33.72% | 100.00% | 1 |
| Monthly SPY 40% / cash 60% | 7.52% | 7.59% | -14.09% | 40.12% | 96 |
| VIX equity rule / cash only | 7.74% | 6.04% | -7.05% | 40.17% | 111 |
| Monthly SPY 40 / GLD 30 / cash 30 | 11.57% | 9.22% | -15.57% | 40.06% | 96 |
| Monthly SPY 40 / TLT 20 / GLD 20 / cash 20 | 9.39% | 8.87% | -18.34% | 40.12% | 96 |

| Period | Strategy | Return | SPY | TLT | GLD | Cash | Costs | Within-period max drawdown |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2018–2025 | Strategy v1 | 184.38% | 81.65% | -6.54% | 113.10% | 3.31% | -7.14% | -13.32% |
| 2018–2025 | SPY buy-and-hold | 187.33% | 187.38% | 0.00% | 0.00% | 0.00% | -0.05% | -33.72% |
| 2018–2025 | Monthly SPY 40% / cash 60% | 78.35% | 60.79% | 0.00% | 0.00% | 17.63% | -0.08% | -14.09% |
| 2018–2025 | VIX equity rule / cash only | 81.20% | 65.95% | 0.00% | 0.00% | 17.28% | -2.04% | -7.05% |
| 2018–2025 | Monthly SPY 40 / GLD 30 / cash 30 | 139.39% | 68.33% | 0.00% | 61.28% | 9.94% | -0.15% | -15.57% |
| 2018–2025 | Monthly SPY 40 / TLT 20 / GLD 20 / cash 20 | 104.62% | 65.02% | -3.92% | 37.56% | 6.15% | -0.17% | -18.34% |
| 2020 | Strategy v1 | 24.04% | 10.04% | 1.60% | 13.08% | 0.01% | -0.69% | -13.32% |
| 2020 | SPY buy-and-hold | 18.33% | 18.33% | 0.00% | 0.00% | 0.00% | -0.00% | -33.72% |
| 2020 | Monthly SPY 40% / cash 60% | 8.47% | 8.26% | 0.00% | 0.00% | 0.22% | -0.01% | -14.09% |
| 2020 | VIX equity rule / cash only | 6.83% | 6.71% | 0.00% | 0.00% | 0.22% | -0.10% | -6.36% |
| 2020 | Monthly SPY 40 / GLD 30 / cash 30 | 15.87% | 8.85% | 0.00% | 6.92% | 0.11% | -0.01% | -15.57% |
| 2020 | Monthly SPY 40 / TLT 20 / GLD 20 / cash 20 | 17.48% | 9.21% | 3.47% | 4.75% | 0.08% | -0.02% | -13.84% |
| 2022 | Strategy v1 | -7.70% | -6.98% | -1.50% | 0.32% | 0.95% | -0.50% | -12.99% |
| 2022 | SPY buy-and-hold | -18.18% | -18.18% | 0.00% | 0.00% | 0.00% | -0.00% | -24.50% |
| 2022 | Monthly SPY 40% / cash 60% | -6.08% | -7.24% | 0.00% | 0.00% | 1.16% | -0.01% | -9.65% |
| 2022 | VIX equity rule / cash only | -5.92% | -7.07% | 0.00% | 0.00% | 1.28% | -0.13% | -7.05% |
| 2022 | Monthly SPY 40 / GLD 30 / cash 30 | -6.72% | -7.28% | 0.00% | -0.01% | 0.57% | -0.01% | -13.08% |
| 2022 | Monthly SPY 40 / TLT 20 / GLD 20 / cash 20 | -13.47% | -7.14% | -6.66% | -0.03% | 0.36% | -0.01% | -18.25% |
| 2020 v1 drawdown window 2020-03-09 to 2020-03-18 | Strategy v1 | -13.32% | -1.53% | -7.32% | -4.47% | 0.00% | -0.00% | -13.32% |
| 2020 v1 drawdown window 2020-03-09 to 2020-03-18 | SPY buy-and-hold | -12.48% | -12.48% | 0.00% | 0.00% | 0.00% | -0.00% | -16.84% |
| 2020 v1 drawdown window 2020-03-09 to 2020-03-18 | Monthly SPY 40% / cash 60% | -4.63% | -4.64% | 0.00% | 0.00% | 0.01% | -0.00% | -6.45% |
| 2020 v1 drawdown window 2020-03-09 to 2020-03-18 | VIX equity rule / cash only | -1.62% | -1.63% | 0.00% | 0.00% | 0.01% | -0.00% | -2.29% |
| 2020 v1 drawdown window 2020-03-09 to 2020-03-18 | Monthly SPY 40 / GLD 30 / cash 30 | -8.09% | -4.56% | 0.00% | -3.54% | 0.00% | -0.00% | -9.18% |
| 2020 v1 drawdown window 2020-03-09 to 2020-03-18 | Monthly SPY 40 / TLT 20 / GLD 20 / cash 20 | -10.34% | -4.48% | -3.54% | -2.32% | 0.00% | -0.00% | -10.56% |
| 2022 v1 drawdown window 2022-03-08 to 2022-11-03 | Strategy v1 | -12.99% | -3.94% | 0.00% | -9.71% | 0.80% | -0.14% | -12.99% |
| 2022 v1 drawdown window 2022-03-08 to 2022-11-03 | SPY buy-and-hold | -9.84% | -9.84% | 0.00% | 0.00% | 0.00% | -0.00% | -22.09% |
| 2022 v1 drawdown window 2022-03-08 to 2022-11-03 | Monthly SPY 40% / cash 60% | -2.93% | -3.72% | 0.00% | 0.00% | 0.80% | -0.01% | -8.67% |
| 2022 v1 drawdown window 2022-03-08 to 2022-11-03 | VIX equity rule / cash only | -3.43% | -4.34% | 0.00% | 0.00% | 1.00% | -0.09% | -5.57% |
| 2022 v1 drawdown window 2022-03-08 to 2022-11-03 | Monthly SPY 40 / GLD 30 / cash 30 | -9.85% | -3.52% | 0.00% | -6.71% | 0.38% | -0.01% | -13.08% |
| 2022 v1 drawdown window 2022-03-08 to 2022-11-03 | Monthly SPY 40 / TLT 20 / GLD 20 / cash 20 | -13.93% | -3.40% | -6.34% | -4.43% | 0.25% | -0.01% | -16.48% |

## Static allocation cost sensitivity

| Strategy | Cost (bp) | CAGR | Volatility | Max drawdown |
|---|---:|---:|---:|---:|
| Strategy v1 | 0 | 14.65% | 10.51% | -13.32% |
| Strategy v1 | 5 | 14.00% | 10.51% | -13.32% |
| Strategy v1 | 20 | 12.06% | 10.53% | -14.20% |
| Monthly SPY 40 / GLD 30 / cash 30 | 0 | 11.58% | 9.22% | -15.57% |
| Monthly SPY 40 / GLD 30 / cash 30 | 5 | 11.57% | 9.22% | -15.57% |
| Monthly SPY 40 / GLD 30 / cash 30 | 20 | 11.52% | 9.22% | -15.57% |
| Monthly SPY 40 / TLT 20 / GLD 20 / cash 20 | 0 | 9.41% | 8.87% | -18.33% |
| Monthly SPY 40 / TLT 20 / GLD 20 / cash 20 | 5 | 9.39% | 8.87% | -18.34% |
| Monthly SPY 40 / TLT 20 / GLD 20 / cash 20 | 20 | 9.33% | 8.87% | -18.37% |

## Findings

V1 and the monthly 40% SPY benchmark have similar mean equity weights (40.14% and 40.12%), but their returns and volatility differ substantially. V1's 14.00% CAGR exceeds the fixed benchmark's 7.52%, while volatility is higher (10.51% versus 7.59%). Their maximum drawdowns are close (-13.32% versus -14.09%). Thus reduced equity exposure already explains much of the drawdown improvement relative to 100% SPY; it does not by itself explain v1's higher return than the fixed benchmark.

GLD contributed +113.10 percentage points to v1's +184.38% cumulative net return; SPY contributed +81.65 points and TLT -6.54 points. This accounting result identifies gold exposure as a major source of realized gains, without proving that the eligibility rule adds value over a static gold allocation. The cash-only VIX variant returned 7.74% annualized with a -7.05% maximum drawdown; timing and defensive allocation should not be credited as one inseparable effect.

In 2020, v1's calendar return was +24.04%, with GLD contributing +13.08 points. That includes the rebound, so the separate peak-to-trough tables are needed to study crash protection. In 2022, v1 lost 7.70%, worse than the fixed benchmark's -6.08%; its TLT exposure contributed -1.50 points. Defensive assets did not help uniformly. During v1's own 2020-03-09 to 2020-03-18 drawdown, TLT and GLD contributed -7.32 and -4.47 points, respectively. During its 2022-03-08 to 2022-11-03 drawdown, GLD contributed -9.71 points. Gold was a major full-period return source but also a source of substantial interim losses.

## Static allocation extension

At 5 bp, the SPY/GLD/cash fixed portfolio returned 11.57% annualized with 9.22% volatility and a -15.57% maximum drawdown. The four-asset fixed portfolio returned 9.39% with 8.87% volatility and a -18.34% maximum drawdown. V1 returned more than both chosen static portfolios and had a smaller maximum drawdown, but higher volatility. At 20 bp, v1 returned 12.06% versus 11.52% for SPY/GLD/cash: the annualized return gap shrank to about 0.54 percentage points. This comparison does not establish that the dynamic rules outperform all static alternatives.

The two new fixed portfolios retain a 40% SPY target and divide the rest equally between GLD/cash (30% each), or TLT/GLD/cash (20% each). They rebalance monthly. These weights were recorded in docs/static_benchmark_protocol.md before this extension was run; they were not selected through a search. This remains a retrospective exercise because the original final-test and attribution results had already been observed. Consult the cost sensitivity table and chart before interpreting the 5 bp comparison.

## Scope and methods

This is an explanatory analysis performed after observing the 2018–2025 final test. Benchmarks were added after that observation. Results cannot establish a new independent test or a causal effect. No weights or cutoffs were optimized, and strategy v1 rules are unchanged.

The fixed benchmark resets to SPY 40% and cash 60% at the first trading close of each month. The cash-only variant uses the same v1 SPY targets, Friday decisions, next-close execution, and 10-point ETF no-trade threshold, allocating all non-SPY capital to cash. Its rebalance decisions can differ from v1 because defensive ETF changes no longer enter that threshold. This is a diagnostic variant, not a pure single-variable causal experiment.

All portfolios start with capital 1 at the first 2018 session close, use 5 bp costs per traded dollar, and use the same adjusted prices and cash proxy as the main backtest. The initial purchase is charged and terminal liquidation is not. Cash uses the prior session's lagged DGS3MO rate divided by 252. Adjusted-close execution, secondary ETF data, and omitted taxes limit realism.

Each asset contribution sums its dollar P&L from pre-return holdings and divides by period-start capital. Costs are a separate negative contribution. Contributions sum exactly to net cumulative return; these are not annualized return contributions or causal effects. Later gains on earlier profits are attributed to the assets holding those profits at that time. The two drawdown windows are selected retrospectively from v1 within each calendar year, and all portfolios are compared over those same dates. They do not represent each benchmark's own worst interval. Calendar-year returns include the move from the previous year-end close. Within-period drawdown resets its high-water mark at the previous year-end, unlike full-history drawdown. Mean SPY weight averages holdings entering close-to-close intervals.

A 40% SPY benchmark is a simple reference, not an exact exposure or volatility match. Differences from v1 combine equity timing, defensive holdings, drift, and trading costs. A lower drawdown alone does not prove value from the dynamic rules.

## Checks

Daily asset P&L minus costs reconciles exactly to changes in net wealth. Period contributions reconcile to net returns. Existing v1 and SPY final-test results match the previously published metrics exactly.
