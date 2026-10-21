"""Generate the final English report and publication-friendly figures from saved results."""
from pathlib import Path
import base64
import csv
import hashlib
import html
import json
import os
os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parents[1] / '.matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import date
from report_findings import backtest_findings, performance_findings

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports'; FIG=OUT/'figures'; FIG.mkdir(exist_ok=True)
back=json.loads((OUT/'backtest_v1_summary.json').read_text())
perf=json.loads((OUT/'performance_analysis_summary.json').read_text())
eda=json.loads((OUT/'initial_analysis_summary.json').read_text())
manifest=json.loads((ROOT/'data/raw/sources.json').read_text())
audit=json.loads((OUT/'review_checks.json').read_text())
assert audit['status']=='passed'
summary=perf['comparison']; names={r['strategy']:r for r in summary}
v=names['Strategy v1']; spy=names['SPY buy-and-hold']; gold=names['Monthly SPY 40 / GLD 30 / cash 30']
findings=performance_findings(summary,perf['attribution'],perf['static_cost_sensitivity'])
paths={}
with (OUT/'performance_daily_pnl.csv').open() as f:
    for row in csv.DictReader(f):
        paths.setdefault(row['strategy'],[]).append((date.fromisoformat(row['date']),float(row['net_value'])))
colors=['#2059b3','#74849a','#b77b21','#138778']
choices=[('Strategy v1','Strategy v1'),('SPY buy-and-hold','SPY buy-and-hold'),('Monthly SPY 40 / GLD 30 / cash 30','40% SPY / 30% gold / 30% cash'),('Monthly SPY 40% / cash 60%','40% SPY / 60% cash')]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold'})
charts={}
def save(key,fig,caption):
    fig.tight_layout()
    fig.savefig(FIG/f'final_{key}.png',dpi=170,bbox_inches='tight',facecolor='white')
    fig.savefig(FIG/f'final_{key}.svg',bbox_inches='tight',facecolor='white')
    plt.close(fig);charts[key]=caption
for key in ('wealth','drawdown'):
    fig,ax=plt.subplots(figsize=(10,4.5))
    for (name,label),color in zip(choices,colors):
        points=paths[name]; ds=[p[0] for p in points]; vals=[p[1] for p in points]
        if key=='drawdown':
            peak=1.; ys=[]
            for value in vals:
                peak=max(peak,value);ys.append(100*(value/peak-1))
        else: ys=vals
        ax.plot(ds,ys,label=label,color=color,lw=1.6)
    ax.set_ylabel('Initial capital = 1' if key=='wealth' else 'Drawdown (%)')
    ax.set_title('Final test: portfolio value after costs' if key=='wealth' else 'Final test: loss below prior portfolio peak')
    ax.xaxis.set_major_locator(mdates.YearLocator(2));ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.grid(axis='y',alpha=.2);ax.legend(loc='upper left',frameon=False,fontsize=9)
    save(key,fig,'2018-01-02–2025-12-31. All portfolios use 5 bp costs per traded ETF dollar, including their initial purchase. Static allocations rebalance monthly.')
fig,ax=plt.subplots(figsize=(10,4.4))
a=next(r for r in perf['attribution'] if r['period']=='2018–2025' and r['strategy']=='Strategy v1')
assets=['SPY','TLT','GLD','Cash','Costs']; vals=[a[k]*100 for k in assets]
ax.bar(assets,vals,color=['#2059b3','#74849a','#b77b21','#138778','#bc5347'])
for x,y in enumerate(vals):ax.annotate(f'{y:+.2f}',(x,y),xytext=(0,5 if y>=0 else -15),textcoords='offset points',ha='center')
ax.axhline(0,color='#667',lw=.7);ax.set_ylabel('Percentage points of initial capital');ax.set_title('V1 cumulative return: asset P&L and charges');ax.margins(y=.18)
save('attribution',fig,f"Contributions add to {a['return']:+.2%} cumulative net return. They are not contributions to annualized return and do not estimate causal effects.")
fig,ax=plt.subplots(figsize=(10,4.3))
for (name,label),color in zip([choices[0],choices[2],('Monthly SPY 40 / TLT 20 / GLD 20 / cash 20','40% SPY / 20% TLT / 20% gold / 20% cash')],[colors[0],colors[2],colors[3]]):
    cs=[r for r in perf['static_cost_sensitivity'] if r['strategy']==name]
    ax.plot([r['bps'] for r in cs],[100*r['cagr'] for r in cs],marker='o',label=label,color=color)
ax.set(xlabel='Basis points per traded ETF dollar',ylabel='Annualized net return (%)',title='Cost sensitivity after the final test');ax.set_xticks([0,5,20]);ax.grid(axis='y',alpha=.2);ax.legend(frameon=False,fontsize=9)
save('costs',fig,'Aggregate friction scenarios apply to buys and sells. No separate spread, market impact, tax, or additional execution-delay simulation is included.')

md=['# SPY_analysis — Final research report\n\nReviewed 22 October 2026 · Rule-based allocation · Historical data through 31 December 2025\n']
sections=[]
def section(slug,title):
    md.append('\n## '+title+'\n');sections.append(f'<section id="{slug}"><h2>{html.escape(title)}</h2>')
def para(text):
    md.append('\n'+text+'\n');sections.append('<p>'+html.escape(text)+'</p>')
def table(headers,rows):
    md.append('\n| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(str(c) for c in row)+' |' for row in rows)+'\n')
    sections.append('<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+html.escape(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(c))+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table></div>')
def chart(key):
    md.append(f'\n![{key}](figures/final_{key}.png)\n\n{charts[key]}\n')
    encoded=base64.b64encode((FIG/f'final_{key}.png').read_bytes()).decode()
    sections.append(f'<figure><img src="data:image/png;base64,{encoded}" alt="{key}"><figcaption>{html.escape(charts[key])}</figcaption></figure>')
def end():sections.append('</section>')
section('assessment','1. Research assessment')
para(backtest_findings(back))
para('The result is consistent with useful risk reduction in this historical sample. Lower equity exposure already provides substantial drawdown reduction, and gold accounts for much of v1’s cumulative gain. The study does not establish statistically significant alpha, causal value from each rule, or superiority to all static allocations. The implementation is a deterministic rule strategy; no AI or machine-learning model is trained.')
para('This report closes the current research iteration. Final-test results have been observed, and all additional benchmark comparisons are retrospective. The remaining data and execution limitations are recorded below rather than treated as completed validation.')
end()
section('design','2. Data, motivation, and strategy')
para(f"The locally saved dataset contains {manifest['processed']['rows']:,} trading sessions, {manifest['processed']['first_date']}–{manifest['processed']['last_date']}. ETF adjusted closes come from a pinned secondary mirror of a Yahoo Finance cache. VIX and three-month Treasury yields come from FRED. Current VIX has no missing rows; current Treasury rates have {manifest['processed']['missing_rate']} gaps. Lagged macro inputs carry only the latest earlier available value; the first row is unavailable.")
para(f"The development analysis covers {eda['development_rows']:,} sessions through 2015. Median next-20-session SPY volatility was {eda['vix_low_forward_vol_median_pct']:.1f}% in the bottom lagged-VIX quartile and {eda['vix_high_forward_vol_median_pct']:.1f}% in the top quartile ({eda['vix_low_n']} and {eda['vix_high_n']} month-ends). This descriptive association motivates a risk input, not a return-direction forecast. The rule thresholds are experimental choices, not estimated optima.")
table(['Component','Rule'],[
['Equity risk','Lagged VIX below the trailing 33rd percentile / between thresholds / above the 67th percentile maps to 65% / 40% / 15% SPY. Reference window: 252 sessions.'],
['TLT eligibility','Positive trailing 63-session return and trailing 63-session SPY/TLT daily-return correlation below −0.15.'],
['GLD eligibility','Positive trailing 63-session return.'],
['Remainder','Divide equally between eligible TLT/GLD; use cash if neither qualifies.'],
['Trading','Decide after trading Friday close; execute at the next session close. Skip when total absolute ETF-weight change is below 10 percentage points. Holiday Fridays are skipped.']])
para('The final-test and validation portfolios each restart from cash. Their first close allocation uses the preceding session’s signal, an explicit boundary exception to the Friday schedule. Historical data before each evaluation start initialize signals. Subsequent returns are earned by holdings already in place before the current close’s trades.')
end()
section('protocol','3. Evaluation and accounting')
table(['Stage','Dates','Interpretation'],[['Development','2007–2015; portfolio from 2008-01-07','Used to design rules; 252-session initialization.'],['Validation','2016-01-04–2017-12-29','Observed before final test; rules retained.'],['Final test','2018-01-02–2025-12-31','V1 rules retained; now observed.'],['Additional comparisons','Same 2018–2025 dates','Retrospective cash and gold-inclusive diagnostics.']])
para('All portfolios use adjusted-close simple returns, fractional holdings, identical evaluation dates, and costs on both purchases and sales. The post-cost portfolio value solves V_after = V_before − cost_rate × Σ|target_weight × V_after − existing_ETF_value|. Initial purchases are charged; terminal liquidation is not. No external capital is added.')
para('Cash accrues once per close-to-close interval at the previous row’s already lagged DGS3MO rate divided by 100 and 252. Relative to the return-end date, this normally uses a two-session-old rate, and older observations across source gaps. It is a conservative information lag and a yield-based proxy, not a tradable Treasury or deposit total return. Weekend calendar accrual is approximated by the trading-session convention.')
para('Annualized return is final wealth raised to 252 divided by the number of close-to-close intervals, minus one. Volatility is sample standard deviation of daily net returns times √252. The initial purchase cost is included in final wealth and drawdown but excluded from the daily-volatility series. Maximum drawdown starts from initial capital 1. Rebalance counts refer to events, not individual ETF orders.')
end()
section('results','4. Final-test results')
rows_table=[[r['strategy'],f"{r['cagr']:.2%}",f"{r['volatility']:.2%}",f"{r['max_drawdown']:.2%}",f"{r['mean_spy_weight']:.2%}",r['trades']] for r in summary]
table(['Strategy','Annualized return','Volatility','Max drawdown','Mean SPY weight','Rebalances'],rows_table)
para('The table uses 5 bp per traded dollar. Fixed portfolios rebalance monthly. The two gold-inclusive targets use 40% SPY and divide the remainder equally across GLD/cash or TLT/GLD/cash. These weights were defined before their own runs but after the original final-test results had been seen. They are not an exact volatility or full-exposure match for v1.')
chart('wealth');chart('drawdown');para(findings[0]);end()
section('attribution','5. Where gains and losses arose')
chart('attribution');para(findings[1]);para(findings[2])
years=[r for r in perf['attribution'] if r['period'] in ('2020','2022') and r['strategy'] in ('Strategy v1','SPY buy-and-hold','Monthly SPY 40% / cash 60%')]
table(['Year','Portfolio','Calendar return','Within-year max drawdown'],[[r['period'],r['strategy'],f"{r['return']:+.2%}",f"{r['within_period_drawdown']:.2%}"] for r in years])
para('Calendar-year returns begin at the preceding year-end close. Within-year drawdowns reset the high-water mark there. Asset contributions sum dollar P&L and divide by period-start capital, with costs shown separately. Later gains on reinvested profits belong to the asset holding that capital. Selected peak-to-trough dates are v1’s worst interval within the year; they are not each benchmark’s own worst interval. The cash-only VIX variant also changes the no-trade decisions, because defensive ETF turnover disappears, so it is not a clean single-rule ablation.')
end()
section('costs','6. Costs and robustness limits')
chart('costs');para(findings[3])
para('Testing a few static portfolios does not exhaust the alternatives. No formal significance test, confidence interval for excess performance, or correction for repeated strategy comparisons is reported. An extra-session execution delay, raw-price tradable execution, broader parameter stability checks, and a full independent price-history comparison remain unperformed. These are limitations of the completed study, not evidence that the strategy would or would not survive them.')
end()
section('review','7. Review, corrections, and checks')
table(['Finding','Correction or disposition'],[
['Stale evaluation status','Updated initial-analysis and README wording to reflect completed validation and final testing.'],
['Hardcoded result prose','Narrative figures now come from the same results as the tables, preventing silent disagreement after reruns.'],
['Mutable redownloads','Cached source files are verified against the manifest; changing the snapshot requires explicit refresh. An absent cache must match recorded hashes or fail.'],
['Input assumptions','The engine rejects unknown modes, invalid costs, too-short runs, nonfinite prices/macro values, and unordered dates. Signal warmup is enforced.'],
['Cash timing ambiguity','Documented the prior row’s already lagged input explicitly; historical accounting is preserved.'],
['Source and execution limits','Recorded as unresolved. No claim of fully verified ETF history or executable investment performance.']])
para(f"The review pipeline passed {audit['unit_tests']} focused automated tests, plus source/processed hash checks, daily and period P&L reconciliation, historical-prefix checks, and a comparison against the previously saved backtest metrics. Published backtest numerical results were unchanged: {str(audit['backtest_metrics_unchanged']).lower()}. Tests cover intended mechanics, not profitability or source truth.")
para('The preserved processed-data SHA-256 is '+manifest['processed']['sha256']+'. A checksum identifies a snapshot; it cannot certify that its market prices are correct. FRED downloads are current historical series, not a full point-in-time vintage archive. A lag alone cannot remove any later data revisions.')
end()
section('conclusion','8. Conclusion')
para(f"V1 is a reproducible allocation experiment with historical annualized return {v['cagr']:.2%}, volatility {v['volatility']:.2%}, and maximum drawdown {v['max_drawdown']:.2%} in the final sample at 5 bp. Its main research contribution is an explicit, inspectable link between risk signals, changing holdings, trading costs, and asset-level P&L.")
para('The evidence supports a narrower conclusion than “the strategy beats the market”: lower equity exposure accounts for substantial risk reduction, gold exposure contributes much of the realized gain, and trading costs reduce the advantage over simple gold-inclusive allocations. Defensive assets also caused sizable interim losses. The project is complete as a historical research prototype; deployment readiness has not been established.')
end()
section('reproduce','9. Reproduction and supporting material')
para('Create a virtual environment, install requirements-visuals.txt, and run .venv/bin/python scripts/rebuild_project.py. The default uses verified cached downloads; a fresh clone attempts to recover the recorded bytes. If mutable FRED data no longer match the manifest, exact reproduction requires the original saved snapshot. Explicit --refresh in download_data.py creates a new data snapshot and must be treated as a new data revision.')
code='python3 -m venv .venv\n.venv/bin/python -m pip install -r requirements-visuals.txt\n.venv/bin/python scripts/rebuild_project.py\npython3 -m http.server 8765 --bind 127.0.0.1 --directory reports'
md.append('\n```bash\n'+code+'\n```\n');sections.append('<pre>'+html.escape(code)+'</pre>')
links=[('Initial analysis','initial_analysis.html'),('Backtest details','backtest_v1.html'),('Attribution and all benchmark charts','performance_analysis.html'),('Review checks','review_checks.json')]
md.append('\n'+ '\n'.join('- ['+n+']('+u+')' for n,u in links)+'\n');sections.append('<ul>'+''.join('<li><a href="'+u+'">'+n+'</a></li>' for n,u in links)+'</ul>')
para('Figures are available as PNG and SVG under reports/figures/final_*. The HTML report embeds its figures and can be read offline; supporting links require the adjacent project files. Raw and processed CSV downloads are excluded from Git. No live brokerage or scheduled trading process is configured.')
end()
section('sources','10. Sources and provenance')
sources=[('Pinned ETF data mirror','https://github.com/manisahni/marketdata/tree/'+manifest['etf_source_commit']),('FRED VIXCLS','https://fred.stlouisfed.org/series/VIXCLS'),('FRED DGS3MO','https://fred.stlouisfed.org/series/DGS3MO')]
for title,url in sources:
    md.append('\n- ['+title+']('+url+')\n');sections.append('<p><a href="'+url+'">'+title+'</a></p>')
para('The source manifest records URLs, retrieval time, raw-file hashes, and the processed-data hash. The original seed paper was not used as the strategy specification; the implemented rules and evaluation history are documented in this repository.')
end()
(OUT/'final_report.md').write_text('\n'.join(md),encoding='utf-8')
css='''*{box-sizing:border-box}body{margin:0;background:#f3f5f8;color:#1c3047;font:16px/1.65 system-ui,-apple-system,sans-serif}main{max-width:1120px;margin:auto;padding:36px 24px}header{padding:32px 0 22px}h1{font-size:42px;line-height:1.15;margin:10px 0}h2{font-size:25px;line-height:1.3;margin:0 0 18px}p{max-width:960px}.eyebrow{font-size:12px;font-weight:700;letter-spacing:.12em;color:#2059b3}.meta{color:#586a80}nav{display:flex;gap:9px;flex-wrap:wrap;margin:22px 0}nav a,.button{padding:7px 12px;border:1px solid #cfd8e5;border-radius:6px;background:white}a{color:#2059b3}section{background:white;border:1px solid #dfe5ed;border-radius:12px;margin:20px 0;padding:28px}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:11px;border-bottom:1px solid #e1e6ed;text-align:left;vertical-align:top}th{background:#eef3fa}figure{margin:22px 0}img{max-width:100%;height:auto;display:block}figcaption{font-size:13px;color:#586a80;margin-top:10px}pre{background:#eef3fa;padding:16px;overflow:auto;font-size:13px}.callout{border-left:4px solid #2059b3;padding:12px 18px;background:#edf3fc}footer{font-size:13px;color:#586a80;padding:20px}@media(max-width:650px){main{padding:16px 10px}h1{font-size:30px}section{padding:18px 12px}h2{font-size:22px}}@media print{body{background:white;font-size:11pt}main{padding:0;max-width:none}nav{display:none}section{border:0;padding:10px 0;break-inside:auto}figure,table{break-inside:avoid}h2{break-after:avoid}a{color:inherit}header{padding-top:0}}'''
nav=''.join(f'<a href="#{slug}">{label}</a>' for slug,label in [('assessment','Assessment'),('results','Results'),('attribution','Attribution'),('costs','Costs'),('review','Review'),('reproduce','Reproduce')])
header='<header><div class="eyebrow">SPY_ANALYSIS / FINAL RESEARCH REPORT</div><h1>Risk-aware ETF allocation</h1><p class="meta">Reviewed 22 October 2026 · SPY / TLT / GLD / cash · Final sample: 2018–2025</p><p class="callout">Historical risk reduction is visible. Its sources, cost sensitivity, and limits matter as much as the headline return.</p><nav>'+nav+'</nav></header>'
(OUT/'final_report.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SPY_analysis — Final research report</title><style>'+css+'</style></head><body><main>'+header+''.join(sections)+'<footer>Research snapshot. Open the supporting reports for full tables and interactive charts.</footer></main></body></html>',encoding='utf-8')
print('Built final_report.md, final_report.html, and four PNG/SVG figures.')
