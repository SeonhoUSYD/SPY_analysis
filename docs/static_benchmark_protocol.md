# Static allocation diagnostic protocol

This extension is defined after the v1 final test and attribution have been observed. It is a retrospective benchmark comparison, not an independent test. No allocation search or ranking-based parameter selection is performed.

Two transparent monthly target portfolios are added before calculating their results:

- **SPY 40% / GLD 30% / cash 30%:** retains the existing 40% equity reference and divides the remaining capital equally between gold and cash.
- **SPY 40% / TLT 20% / GLD 20% / cash 20%:** retains 40% equity and divides the remaining capital equally across the three other v1 assets.

Each portfolio rebalances at the first trading close of each month, starts from cash at the first 2018 close, and uses the existing accounting engine and data. Evaluate 0, 5, and 20 bp costs per traded dollar. Charge the initial purchase and omit terminal liquidation, consistently with the existing report. Do not alter v1 rules.

Compare annualized returns, volatility, maximum drawdown, holdings, asset P&L, and the existing 2020/2022 episodes. A static portfolio need not match v1's average non-equity weights or volatility. Relative performance describes these choices and this observed sample; it does not isolate a causal effect of timing or establish a globally optimal allocation.
