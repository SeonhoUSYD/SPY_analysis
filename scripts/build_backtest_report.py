"""Evaluate frozen strategy v1 on development, validation, and the authorized final test."""
from pathlib import Path
import csv
import json
import plotly.graph_objects as go
from backtest_strategy_v1 import load, run, signal

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports'
MODES = {'v1': 'Strategy v1', 'spy': 'SPY buy-and-hold', 'equal': 'Monthly equal weight'}
rows = load('2025-12-31')
assert rows[-1]['date'] == '2025-12-31'
first = next(i for i in range(252, len(rows)-1) if rows[i]['day'].weekday() == 4) + 1
validation = next(i for i, r in enumerate(rows) if r['date'] >= '2016-01-01')
final_start = next(i for i, r in enumerate(rows) if r['date'] >= '2018-01-01')
validation_rows = rows[:final_start]
# Prefix invariance: future observations must not change historical holdings or wealth.
short = rows[:validation]
a = run(short, first, 'v1', .0005)
b = run(rows, first, 'v1', .0005)
assert a['values'] == b['values'][:len(a['values'])]
assert a['weights'] == b['weights'][:len(a['weights'])]
for i in (first-1, validation-1, final_start-1):
    assert signal(rows, i) == signal(rows[:i+1], i)

results = []
figs = []
paths = []
for period, sample, start in [('Development', short, first), ('Validation', validation_rows, validation), ('Final test', rows, final_start)]:
    # Each period starts with fresh capital and cash; history is used only for signals.
    dates = [r['date'] for r in sample[start:]]
    wealth = go.Figure()
    drawdown = go.Figure()
    for bps in (0, 5, 20):
        for mode, name in MODES.items():
            result = run(sample, start, mode, bps / 10000)
            values = result.pop('values')
            weights = result.pop('weights')
            result.update(period=period, strategy=name, bps=bps)
            results.append(result)
            if bps == 5:
                wealth.add_scatter(x=dates, y=values, name=name)
                peak = 1.0
                dd = []
                for v in values:
                    peak = max(peak, v)
                    dd.append(v / peak - 1)
                drawdown.add_scatter(x=dates, y=dd, name=name)
                for d, v, w in zip(dates, values, weights):
                    paths.append([period, name, d, v, *w])
                if mode == 'v1':
                    allocation = go.Figure()
                    for j, asset in enumerate(('SPY', 'TLT', 'GLD', 'Cash')):
                        allocation.add_scatter(x=dates, y=[w[j] for w in weights], name=asset, stackgroup='one')
                    allocation.update_layout(title=f'{period}: strategy v1 holdings after close', yaxis_tickformat='.0%', yaxis_range=[0, 1])
    wealth.update_layout(title=f'{period}: net portfolio value (5 bp per traded dollar)', yaxis_title='Initial capital = 1')
    drawdown.update_layout(title=f'{period}: drawdown (5 bp)', yaxis_tickformat='.0%')
    figs.extend([wealth, drawdown, allocation])

cost = go.Figure()
for period in ('Development', 'Validation', 'Final test'):
    for name in MODES.values():
        selected = [r for r in results if r['period'] == period and r['strategy'] == name]
        cost.add_scatter(x=[r['bps'] for r in selected], y=[r['cagr'] for r in selected], mode='lines+markers', name=f'{period}: {name}')
cost.update_layout(title='Cost sensitivity: annualized net returns', xaxis_title='Basis points per traded dollar', yaxis_tickformat='.1%')
figs.append(cost)
for fig in figs:
    fig.update_layout(template='plotly_white', height=430, margin=dict(l=65,r=25,t=75,b=50), hovermode='x unified', legend=dict(orientation='h', y=-.2))

header = '| Period | Cost (bp) | Strategy | CAGR | Volatility | Max drawdown | Rebalances | Costs / initial capital |\n|---|---:|---|---:|---:|---:|---:|---:|'
table = '\n'.join(f"| {r['period']} | {r['bps']} | {r['strategy']} | {r['cagr']:.2%} | {r['volatility']:.2%} | {r['max_drawdown']:.2%} | {r['trades']} | {r['cost_fraction_initial']:.4f} |" for r in results)
notes = '''## Final-test findings

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
'''
report = '# Frozen strategy v1 backtest\n\n' + header + '\n' + table + '\n\n' + notes
(OUT / 'backtest_v1.md').write_text(report)
(OUT / 'backtest_v1_summary.json').write_text(json.dumps(results, indent=2))
with (OUT / 'backtest_v1_paths.csv').open('w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['period','strategy','date','net_value','spy_weight','tlt_weight','gld_weight','cash_weight'])
    writer.writerows(paths)
html = ['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SPY_analysis | Strategy v1 backtest</title><style>body{font:16px system-ui;max-width:1150px;margin:32px auto;padding:0 20px;color:#192a3c;background:#f6f8fb}section{background:white;padding:18px;margin:22px 0;border-radius:12px}p{line-height:1.6}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:9px;border-bottom:1px solid #ddd;text-align:right}td:first-child,td:nth-child(3){text-align:left}</style><h1>Strategy v1: frozen-rule backtest</h1><p>Development, 2016–2017 validation, and the frozen-strategy 2018–2025 final test. All returns are research simulations.</p>']
html.append('<section style="overflow:auto"><table><tr>' + ''.join('<th>'+s+'</th>' for s in ['Period','Cost (bp)','Strategy','CAGR','Volatility','Max drawdown','Rebalances']) + '</tr>')
for r in results:
    if r['bps'] == 5:
        html.append(f"<tr><td>{r['period']}</td><td>5</td><td>{r['strategy']}</td><td>{r['cagr']:.2%}</td><td>{r['volatility']:.2%}</td><td>{r['max_drawdown']:.2%}</td><td>{r['trades']}</td></tr>")
html.append('</table></section>')
for i, fig in enumerate(figs):
    html.append('<section>'+fig.to_html(full_html=False, include_plotlyjs=True if i==0 else False, config={'displaylogo':False,'responsive':True,'modeBarButtons':[['toImage'],['zoom2d','pan2d'],['zoomIn2d','zoomOut2d','autoScale2d','resetScale2d']]})+'</section>')
html.append('<section><h2>Execution and limitations</h2><p>Friday close decisions execute at the following session close. Periods restart in cash, with an initial allocation based on the previous session. Both buys and sells incur costs. Adjusted prices and Treasury-yield cash accrual are approximations. No taxes, fund fees beyond adjusted price returns, or separate market impact model. See backtest_v1.md for the full protocol.</p><p>The final test is now observed. Results describe this historical sample, not guaranteed future performance. Changes informed by these results require a new version and a new evaluation plan.</p></section></html>')
(OUT / 'backtest_v1.html').write_text('\n'.join(html))
print(header + '\n' + '\n'.join(line for line in table.splitlines() if '| 5 |' in line))
print('PASS: prefix invariance, signal causality, positive wealth, normalized weights, isolated evaluation periods')
