"""Post-test attribution and transparent benchmark diagnostics; no optimization."""
import csv
import json
from pathlib import Path
import statistics
import plotly.graph_objects as go
from backtest_strategy_v1 import load, run

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports'
rows = load('2025-12-31')
start = next(i for i, r in enumerate(rows) if r['date'] >= '2018-01-01')
dates = [r['date'] for r in rows[start:]]
names = {'v1':'Strategy v1','spy':'SPY buy-and-hold','fixed40':'Monthly SPY 40% / cash 60%','dynamic_cash':'VIX equity rule / cash only','gold_cash':'Monthly SPY 40 / GLD 30 / cash 30','balanced40':'Monthly SPY 40 / TLT 20 / GLD 20 / cash 20'}
results = {mode:run(rows,start,mode,.0005) for mode in names}
prior = json.loads((OUT/'backtest_v1_summary.json').read_text())
for mode in ('v1','spy'):
    old = next(r for r in prior if r['period']=='Final test' and r['bps']==5 and r['strategy']==names[mode])
    for key in ('final','cagr','volatility','max_drawdown','trades','cost_fraction_initial'):
        assert old[key] == results[mode][key], key
for r in results.values():
    previous = 1.0
    for v, pnl, charge in zip(r['values'],r['pnl'],r['costs']):
        assert abs(v - previous - sum(pnl) + charge) < 1e-12
        previous = v

sensitivity=[]
for mode in ('v1','gold_cash','balanced40'):
    for bps in (0,5,20):
        r=results[mode] if bps==5 else run(rows,start,mode,bps/10000)
        sensitivity.append({'strategy':names[mode],'bps':bps,'cagr':r['cagr'],'volatility':r['volatility'],'max_drawdown':r['max_drawdown']})
figs=[]
wealth=go.Figure(); ddfig=go.Figure()
for mode, name in names.items():
    r=results[mode]
    wealth.add_scatter(x=dates,y=r['values'],name=name)
    peak=1.; dd=[]
    for v in r['values']:
        peak=max(peak,v); dd.append(v/peak-1)
    ddfig.add_scatter(x=dates,y=dd,name=name)
wealth.update_layout(title='2018–2025: net wealth, 5 bp trading costs',yaxis_title='Initial capital = 1')
ddfig.update_layout(title='2018–2025: drawdown comparison',yaxis_tickformat='.0%')
figs += [wealth,ddfig]
costfig=go.Figure()
for mode in ('v1','gold_cash','balanced40'):
    selected=[r for r in sensitivity if r['strategy']==names[mode]]
    assert all(selected[i]['cagr'] >= selected[i+1]['cagr'] for i in range(2))
    costfig.add_scatter(x=[r['bps'] for r in selected],y=[r['cagr'] for r in selected],mode='lines+markers',name=names[mode])
costfig.update_layout(title='Static allocations versus v1: cost sensitivity',xaxis_title='Basis points per traded dollar',yaxis_tickformat='.1%')
figs.append(costfig)
summary=[]
for mode,name in names.items():
    r=results[mode]
    summary.append({'strategy':name,**{k:r[k] for k in ('cagr','volatility','max_drawdown','trades')},'mean_spy_weight':statistics.mean(w[0] for w in r['weights'][:-1])})

attribution=[]
for label,indices in [('2018–2025',list(range(len(dates)))),('2020',[i for i,d in enumerate(dates) if d.startswith('2020')]),('2022',[i for i,d in enumerate(dates) if d.startswith('2022')])]:
    chart=go.Figure()
    for mode,name in names.items():
        r=results[mode]; base = r['values'][indices[0]-1] if indices[0]>0 else 1.
        contributions=[sum(r['pnl'][i][j] for i in indices)/base for j in range(4)]
        contributions.append(-sum(r['costs'][i] for i in indices)/base)
        ret=r['values'][indices[-1]]/base-1
        assert abs(sum(contributions)-ret)<1e-10
        peak=base; mdd=0.
        for i in indices:
            peak=max(peak,r['values'][i]); mdd=min(mdd,r['values'][i]/peak-1)
        attribution.append({'period':label,'strategy':name,'return':ret,'within_period_drawdown':mdd,**dict(zip(('SPY','TLT','GLD','Cash','Costs'),contributions))})
        chart.add_bar(x=['SPY','TLT','GLD','Cash','Costs'],y=contributions,name=name)
    chart.update_layout(title=f'{label}: additive P&L contributions',yaxis_tickformat='.0%',barmode='group')
    figs.append(chart)
    if label in ('2020','2022'):
        episode=go.Figure()
        for mode,name in names.items():
            r=results[mode]; base=r['values'][indices[0]-1]
            episode.add_scatter(x=[dates[i] for i in indices],y=[r['values'][i]/base for i in indices],name=name)
        episode.update_layout(title=f'{label}: wealth relative to previous year-end',yaxis_title='Previous year-end = 1')
        figs.append(episode)

# Attribute the exact v1 peak-to-trough decline, not the full-year rebound.
for year in ('2020','2022'):
    indices=[i for i,d in enumerate(dates) if d.startswith(year)]
    r=results['v1']; peak=r['values'][indices[0]-1]; peak_i=indices[0]-1
    worst=0.; window=None
    for i in indices:
        if r['values'][i]>peak:
            peak=r['values'][i]; peak_i=i
        decline=r['values'][i]/peak-1
        if decline<worst:
            worst=decline; window=(peak_i,i)
    left,right=window
    label=f"{year} v1 drawdown window {dates[left]} to {dates[right]}"
    chart=go.Figure()
    for mode,name in names.items():
        r=results[mode]; base=r['values'][left]
        contributions=[sum(r['pnl'][i][j] for i in range(left+1,right+1))/base for j in range(4)]
        contributions.append(-sum(r['costs'][i] for i in range(left+1,right+1))/base)
        ret=r['values'][right]/base-1
        assert abs(sum(contributions)-ret)<1e-10
        peak=base; mdd=0.
        for i in range(left+1,right+1):
            peak=max(peak,r['values'][i]); mdd=min(mdd,r['values'][i]/peak-1)
        attribution.append({'period':label,'strategy':name,'return':ret,'within_period_drawdown':mdd,**dict(zip(('SPY','TLT','GLD','Cash','Costs'),contributions))})
        chart.add_bar(x=['SPY','TLT','GLD','Cash','Costs'],y=contributions,name=name)
    chart.update_layout(title=f'{year}: P&L during v1 peak-to-trough decline',yaxis_tickformat='.0%',barmode='group')
    figs.append(chart)

head='| Strategy | CAGR | Volatility | Max drawdown | Mean SPY weight | Rebalances |\n|---|---:|---:|---:|---:|---:|'
body='\n'.join(f"| {r['strategy']} | {r['cagr']:.2%} | {r['volatility']:.2%} | {r['max_drawdown']:.2%} | {r['mean_spy_weight']:.2%} | {r['trades']} |" for r in summary)
attrhead='| Period | Strategy | Return | SPY | TLT | GLD | Cash | Costs | Within-period max drawdown |\n|---|---|---:|---:|---:|---:|---:|---:|---:|'
attrbody='\n'.join('| '+r['period']+' | '+r['strategy']+' | '+' | '.join(f"{r[k]:.2%}" for k in ('return','SPY','TLT','GLD','Cash','Costs','within_period_drawdown'))+' |' for r in attribution)
methods='''## Findings

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
'''
costtable='\n\n## Static allocation cost sensitivity\n\n| Strategy | Cost (bp) | CAGR | Volatility | Max drawdown |\n|---|---:|---:|---:|---:|\n'+'\n'.join(f"| {r['strategy']} | {r['bps']} | {r['cagr']:.2%} | {r['volatility']:.2%} | {r['max_drawdown']:.2%} |" for r in sensitivity)
(OUT/'performance_analysis.md').write_text('# Performance attribution and simple benchmarks\n\n'+head+'\n'+body+'\n\n'+attrhead+'\n'+attrbody+costtable+'\n\n'+methods)
(OUT/'performance_analysis_summary.json').write_text(json.dumps({'comparison':summary,'attribution':attribution,'static_cost_sensitivity':sensitivity},indent=2))
with (OUT/'performance_attribution.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(attribution[0])); writer.writeheader(); writer.writerows(attribution)
with (OUT/'performance_daily_pnl.csv').open('w',newline='') as f:
    writer=csv.writer(f); writer.writerow(['strategy','date','net_value','spy_pnl','tlt_pnl','gld_pnl','cash_pnl','cost'])
    for mode,name in names.items():
        r=results[mode]
        writer.writerows([name,d,v,*p,c] for d,v,p,c in zip(dates,r['values'],r['pnl'],r['costs']))
html=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SPY_analysis | Performance attribution</title><style>body{font:16px system-ui;max-width:1150px;margin:32px auto;padding:0 20px;background:#f6f8fb;color:#192a3c}section{background:white;padding:18px;margin:22px 0;border-radius:12px}p{line-height:1.6}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:9px;border-bottom:1px solid #ddd}</style><h1>Performance attribution and simple benchmarks</h1><p>2018–2025, 5 bp costs. Post-test diagnostics, with unchanged v1 rules. Benchmark choices are retrospective.</p><section style="overflow:auto"><table><tr><th>Strategy</th><th>CAGR</th><th>Volatility</th><th>Max drawdown</th><th>Mean SPY weight</th></tr>']
for r in summary:
    html.append('<tr><td>'+r['strategy']+'</td>'+''.join(f'<td>{r[k]:.2%}</td>' for k in ('cagr','volatility','max_drawdown','mean_spy_weight'))+'</tr>')
html.append('</table></section><section><h2>Gold-inclusive static benchmarks</h2><p>At 5 bp, monthly SPY 40% / GLD 30% / cash 30% returns 11.57% annualized with a -15.57% maximum drawdown. Monthly SPY 40% / TLT 20% / GLD 20% / cash 20% returns 9.39% with a -18.34% drawdown. V1 returns more than these two choices but has higher volatility.</p><p>At 20 bp, v1 returns 12.06% versus 11.52% for SPY/GLD/cash. The return gap narrows to about 0.54 percentage points. Weights were not optimized; these are retrospective diagnostics, not a fresh independent test.</p></section><section><h2>What explains the results?</h2><p>V1 and the fixed benchmark average about 40% equity exposure. The fixed benchmark already reduces maximum drawdown to -14.09%, close to v1 at -13.32%. V1 earns more, but also has higher volatility.</p><p>GLD contributes +113.10 percentage points to v1 cumulative net return of +184.38%. This is an additive P&amp;L decomposition, not an annualized contribution or proof that dynamic selection beats static gold exposure.</p><p>Defensive holdings also lose: in v1’s March 2020 peak-to-trough decline, TLT contributes -7.32 points and GLD -4.47 points. In its March–November 2022 decline, GLD contributes -9.71 points. Full-year returns and peak-to-trough losses answer different questions.</p></section>')
for i,fig in enumerate(figs):
    fig.update_layout(template='plotly_white',height=580,margin=dict(l=65,r=25,t=65,b=210),legend=dict(orientation='h',y=-.22),hovermode='x unified')
    html.append('<section>'+fig.to_html(full_html=False,include_plotlyjs=True if i==0 else False,config={'displaylogo':False,'responsive':True,'modeBarButtons':[['toImage'],['zoom2d','pan2d'],['zoomIn2d','zoomOut2d','autoScale2d','resetScale2d']]})+'</section>')
html.append('<section><h2>Reading the attribution</h2><p>Asset dollar P&amp;L divided by period-start capital, plus negative trading charges, sums to net cumulative return. This is an accounting decomposition, not a causal estimate. Calendar-year charts begin at the previous year-end. The fixed benchmark is not an exact risk match; the cash-only variant changes no-trade decisions as well as defensive holdings.</p><p>See performance_analysis.md for the full accounting definitions and tables. This final-test period has already been observed.</p></section></html>')
(OUT/'performance_analysis.html').write_text('\n'.join(html))
print(head+'\n'+body+'\n\n'+attrhead+'\n'+attrbody)
print('PASS: daily and period P&L reconciliation; existing final-test metric invariance')
