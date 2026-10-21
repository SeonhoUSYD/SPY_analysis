"""Build an offline interactive report, figures, and an output-filled notebook."""
from __future__ import annotations

import base64
import html
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "reports" / "figures"
END = "2015-12-31"
ASSETS = ["SPY", "TLT", "GLD"]
COLORS = {"SPY": "#2563eb", "TLT": "#0f766e", "GLD": "#b7791f"}


def main():
    frame = pd.read_csv(ROOT / "data/processed/market_daily.csv", parse_dates=["date"])
    dev = frame.loc[frame.date <= END].set_index("date")
    prices = dev[["spy_adj_close", "tlt_adj_close", "gld_adj_close"]].copy()
    prices.columns = ASSETS
    assert prices.notna().all().all() and prices.index.is_unique
    assert prices.index.max().strftime("%Y-%m-%d") == END
    returns = prices.pct_change(fill_method=None)
    indexed = prices.div(prices.iloc[0]).mul(100)
    drawdown = (prices / prices.cummax() - 1) * 100
    volatility = returns.rolling(21).std(ddof=1) * np.sqrt(252) * 100
    correlation = pd.DataFrame({
        "SPY / TLT": returns.SPY.rolling(126).corr(returns.TLT),
        "SPY / GLD": returns.SPY.rolling(126).corr(returns.GLD),
    })
    monthly = []
    for i in range(len(dev) - 21):
        if dev.index[i].month == dev.index[i+1].month:
            continue
        vix = dev.vix_lag1.iloc[i]
        if pd.isna(vix):
            continue
        future = returns.SPY.iloc[i+1:i+21]
        assert len(future) == 20 and future.index.max() <= pd.Timestamp(END)
        monthly.append({"date": dev.index[i].strftime("%Y-%m-%d"), "vix": vix,
                        "forward_vol": future.std(ddof=1) * np.sqrt(252) * 100})
    monthly = pd.DataFrame(monthly)
    q25, q75 = monthly.vix.quantile([.25, .75])
    low = monthly.loc[monthly.vix <= q25, "forward_vol"]
    high = monthly.loc[monthly.vix >= q75, "forward_vol"]
    stress_threshold = returns.SPY.dropna().quantile(.05)
    stress = returns.loc[returns.SPY <= stress_threshold] * 100
    FIG.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.titleweight": "bold", "savefig.facecolor": "white"})
    panels = []

    def save(slug, title, description, method, figure, ax):
        figure.update_layout(template="plotly_white", height=400,
            font={"family": "system-ui, sans-serif", "size": 13, "color": "#22314a"},
            colorway=list(COLORS.values()), margin={"l": 65, "r": 25, "t": 30, "b": 55},
            legend={"orientation": "h", "y": 1.12}, hovermode="closest")
        for axis in np.atleast_1d(ax):
            axis.grid(axis="y", color="#dce2eb", alpha=.7)
        mpl_figure = np.atleast_1d(ax)[0].figure
        mpl_figure.tight_layout()
        png = FIG / f"initial_{slug}.png"
        mpl_figure.savefig(png, dpi=170, bbox_inches="tight")
        mpl_figure.savefig(FIG / f"initial_{slug}.svg", bbox_inches="tight")
        plt.close(mpl_figure)
        panels.append({"slug": slug, "title": title, "description": description,
                       "method": method, "figure": figure, "png": png})

    def time_panel(data, slug, title, english, ylabel, description, method, zero=False):
        fig, ax = plt.subplots(figsize=(10.5, 4))
        interactive = go.Figure()
        for i, column in enumerate(data.columns):
            color = COLORS.get(column, [COLORS["TLT"], COLORS["GLD"]][i % 2])
            clean = data[column].dropna()
            ax.plot(clean.index, clean, label=column, color=color, lw=1.25)
            interactive.add_trace(go.Scatter(x=clean.index.strftime("%Y-%m-%d").tolist(),
                y=clean.round(5).tolist(), name=column, mode="lines", line={"color": color},
                hovertemplate="%{x}<br>%{y:.2f}<extra>%{fullData.name}</extra>"))
        if zero:
            ax.axhline(0, color="#64748b", lw=.8, ls="--")
            interactive.add_hline(y=0, line_width=1, line_dash="dash", line_color="#94a3b8")
        ax.set(title=english, ylabel=ylabel, xlabel="Date")
        ax.xaxis.set_major_locator(mdates.YearLocator(2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.legend(loc="best", frameon=False)
        interactive.update_xaxes(title_text="Date")
        interactive.update_yaxes(title_text=ylabel)
        save(slug, title, description, method, interactive, ax)
        interactive.update_layout(hovermode="x unified")

    time_panel(indexed, "wealth", "01 · Asset paths from a common starting point",
        "Adjusted-price index | 2007-2015", "Start = 100",
        "Compare equities, long-duration Treasuries, and gold on the same scale. Each index starts at 100; these are asset observations, not strategy returns.",
        "Adjusted close divided by its first observation, multiplied by 100. Cash interest and transaction costs are excluded.")
    time_panel(drawdown, "drawdown", "02 · Losses below each previous peak",
        "Drawdown from previous peak", "Drawdown (%)",
        "High cumulative returns can conceal substantial interim losses. TLT and GLD also experience drawdowns, motivating a test of their defensive role.",
        "Current adjusted price divided by the highest price observed so far, minus one. Peaks before the sample start are excluded.", True)
    time_panel(volatility, "volatility", "03 · Risk changes through time",
        "Rolling 21-session realized volatility", "Annualized volatility (%)",
        "Each asset alternates between quieter and more turbulent periods. This motivates comparing fixed allocations with risk-dependent exposure.",
        "Sample standard deviation of the trailing 21 daily simple returns, multiplied by the square root of 252. This is a backward-looking risk measure.")
    time_panel(correlation, "correlation", "04 · Diversification relationships change",
        "Rolling 126-session return correlations", "Pearson correlation",
        "The strength of the SPY/TLT relationship varies, as does the SPY/GLD relationship. Low correlation alone does not guarantee downside protection.",
        "Pearson correlation of contemporaneous daily returns over the trailing 126 sessions. No future observations enter this calculation.", True)

    fig, ax = plt.subplots(figsize=(10.5, 4))
    ax.scatter(monthly.vix, monthly.forward_vol, color=COLORS["SPY"], alpha=.6, s=24)
    ax.axvline(q25, color=COLORS["TLT"], ls="--", lw=1)
    ax.axvline(q75, color=COLORS["GLD"], ls="--", lw=1)
    ax.set(title="Month-end VIX vs next 20-session volatility", xlabel="VIX (one-session lag)",
           ylabel="Forward SPY volatility (% annualized)")
    interactive = go.Figure(go.Scatter(x=monthly.vix.tolist(), y=monthly.forward_vol.tolist(),
        text=monthly.date.tolist(), mode="markers", marker={"color": COLORS["SPY"], "size": 8, "opacity": .7},
        hovertemplate="%{text}<br>Lagged VIX: %{x:.2f}<br>Forward volatility: %{y:.2f}%<extra></extra>"))
    interactive.add_vline(x=q25, line_dash="dash", line_color=COLORS["TLT"])
    interactive.add_vline(x=q75, line_dash="dash", line_color=COLORS["GLD"])
    interactive.update_xaxes(title_text="Month-end VIX (one-session lag)")
    interactive.update_yaxes(title_text="Next 20-session SPY volatility (% annualized)")
    save("vix_forward", "05 · VIX and subsequent realized risk",
        f"Median subsequent volatility is {low.median():.1f}% in the bottom VIX quartile and {high.median():.1f}% in the top quartile, with {len(low)} and {len(high)} month-end observations. This does not establish return-direction predictability.",
        "Each point is a month-end. VIX is lagged by one session and matched to the annualized standard deviation of the following 20 returns. Some windows may overlap; no causal or significance claim is made.", interactive, ax)

    fig, ax = plt.subplots(figsize=(10.5, 4))
    boxes = ax.boxplot([stress[a].to_numpy() for a in ASSETS], tick_labels=ASSETS,
                      patch_artist=True, showmeans=True)
    for patch, a in zip(boxes["boxes"], ASSETS):
        patch.set_facecolor(COLORS[a]); patch.set_alpha(.35)
    ax.axhline(0, color="#64748b", lw=.8, ls="--")
    ax.set(title=f"Asset returns on {len(stress)} worst-5% SPY days", ylabel="Same-day return (%)")
    interactive = go.Figure()
    for a in ASSETS:
        interactive.add_trace(go.Box(y=stress[a].tolist(), name=a, marker_color=COLORS[a],
                                     boxmean=True, boxpoints="outliers"))
    interactive.add_hline(y=0, line_dash="dash", line_width=1)
    interactive.update_yaxes(title_text="Same-day return (%)")
    save("stress", "06 · Stress-day averages and distributions",
        f"Across {len(stress)} worst-5% SPY days, TLT averaged {stress.TLT.mean():+.2f}% and GLD {stress.GLD.mean():+.2f}%. Dispersion and extreme outcomes matter alongside the average response.",
        f"Days are selected retrospectively using the development-sample fifth percentile of SPY returns ({stress_threshold:.2%}). These are contemporaneous descriptive outcomes, not identifiable trading signals. Boxes show the interquartile range, the central line is the median, and means and outliers are shown separately.", interactive, ax)

    summary = {"development_start": str(dev.index.min().date()), "development_end": END,
        "development_rows": len(dev), "return_rows": len(returns.dropna()),
        "vix_month_ends": len(monthly), "vix_low_n": len(low), "vix_high_n": len(high),
        "vix_low_forward_vol_median_pct": float(low.median()),
        "vix_high_forward_vol_median_pct": float(high.median()),
        "stress_days": len(stress), "stress_spy_threshold": float(stress_threshold),
        "correlations": returns.corr().to_dict(), "figure_count": len(panels)}
    (ROOT / "reports/initial_analysis_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    build_html(dev, panels)
    build_notebook(panels, len(dev), len(returns.dropna()))
    print(json.dumps(summary, indent=2))


def build_html(dev, panels):
    sections = []
    for panel in panels:
        plot = panel["figure"].to_html(full_html=False, include_plotlyjs=False,
            div_id="chart-" + panel["slug"], config={"responsive": True, "displaylogo": False,
                "modeBarButtons": [["toImage"], ["zoom2d", "pan2d"],
                    ["zoomIn2d", "zoomOut2d", "autoScale2d", "resetScale2d"]],
                                                        "toImageButtonOptions": {"format": "png", "scale": 2}})
        sections.append(f'<section id="{panel["slug"]}"><h2>{html.escape(panel["title"])}</h2>'
            f'<p>{html.escape(panel["description"])}</p>{plot}'
            f'<details><summary>Method and interpretation</summary><p>{html.escape(panel["method"])}</p></details></section>')
    nav = "".join(f'<a href="#{p["slug"]}">{p["title"].split(" · ")[1]}</a>' for p in panels)
    template = '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>ETF Initial Analysis</title>
<style>body{margin:0;background:#f5f7fb;color:#22314a;font:16px/1.7 system-ui,-apple-system,sans-serif}main{max-width:1080px;margin:auto;padding:44px 24px}h1{font-size:36px;line-height:1.25;margin:12px 0}h2{font-size:23px;margin:0 0 10px}p{max-width:870px}header{padding:8px 0 26px}.eyebrow{color:#2563eb;letter-spacing:.1em;font-weight:600}.meta{color:#576780}nav{display:flex;flex-wrap:wrap;gap:8px;margin:24px 0}nav a{padding:7px 12px;background:white;border:1px solid #dfe5ef;border-radius:6px}a{color:#1d5cab;text-decoration:none}a:hover{text-decoration:underline}section{background:white;padding:25px;margin:22px 0;border:1px solid #e1e7ef;border-radius:10px;overflow:hidden}details{font-size:14px;color:#53647d;margin-top:12px}summary{cursor:pointer}footer{padding:20px 0 40px;font-size:14px}.note{padding-left:16px;border-left:3px solid #2563eb}.plotly-graph-div{width:100%}@media(max-width:600px){main{padding:24px 12px}section{padding:16px 6px}section h2,section p,section details{margin-left:10px;margin-right:10px}h1{font-size:28px}}</style>
<script>__PLOTLY__</script></head><body><main><header><div class="eyebrow">INITIAL ANALYSIS / ETF ALLOCATION</div>
<h1>When risk changes, do asset roles change?</h1>
<p class="meta">2007-01-03 – 2015-12-31 · __COUNT__ trading sessions · SPY / TLT / GLD</p>
<p class="note">Strategy questions begin with development-period observations. Zoom, pan, and hover to inspect each chart. Data from 2016 onward are excluded from these calculations.</p>
<nav>__NAV__</nav></header>__SECTIONS__
<footer><h2>From observation to experiment</h2><p>The proposed rules use VIX to adjust equity exposure, check recent TLT/GLD behavior, and gate rebalancing. These charts do not establish outperformance or optimal weights. Transaction costs and out-of-sample evaluation are the next checks.</p>
<p>Sources: <a href="https://github.com/manisahni/marketdata/tree/65a079329e379e104495f459e12e76a8f995585a">Pinned ETF adjusted-close mirror</a> · <a href="https://fred.stlouisfed.org/series/VIXCLS">FRED VIXCLS</a> · <a href="https://fred.stlouisfed.org/series/DGS3MO">FRED DGS3MO</a>.</p>
<p>ETF data come from a secondary mirror of a Yahoo Finance cache. Calculations use simple returns and 252 sessions per year. Execution, costs, cash interest, and taxes are excluded from these asset-observation charts. Rebuild: <code>.venv/bin/python scripts/build_initial_analysis.py</code></p></footer></main></body></html>'''
    document = template.replace("__PLOTLY__", get_plotlyjs()).replace("__COUNT__", f"{len(dev):,}")
    document = document.replace("__NAV__", nav).replace("__SECTIONS__", "".join(sections))
    (ROOT / "reports/initial_analysis.html").write_text(document, encoding="utf-8")


def build_notebook(panels, observations, return_observations):
    def markdown(text):
        return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}
    cells = [markdown("# Initial analysis: ETF allocation\n\nDevelopment-period observations for 2007-2015. Data from 2016 onward are excluded. The interactive report is `reports/initial_analysis.html`.\n\nRebuild figures: `.venv/bin/python scripts/build_initial_analysis.py`\n")]
    cells.append({"cell_type": "code", "execution_count": 1, "metadata": {}, "outputs": [],
        "source": ["from pathlib import Path\n", "from IPython.display import Image, display\n",
                   "import pandas as pd\n",
                   "ROOT = Path.cwd()\n", "if ROOT.name == 'notebooks': ROOT = ROOT.parent\n",
                   "market = pd.read_csv(ROOT / 'data/processed/market_daily.csv', parse_dates=['date']).set_index('date')\n",
                   "development = market.loc[:'2015-12-31'].copy()\n",
                   "prices = development[['spy_adj_close', 'tlt_adj_close', 'gld_adj_close']]\n",
                   "daily_returns = prices.pct_change(fill_method=None)\n",
                   "assert development.index.max() <= pd.Timestamp('2015-12-31')\n",
                   "print(f'Development observations: {len(development):,}; return observations: {len(daily_returns.dropna()):,}')\n"]})
    cells[-1]["outputs"] = [{"output_type": "stream", "name": "stdout",
                            "text": [f"Development observations: {observations:,}; return observations: {return_observations:,}\n"]}]
    for i, panel in enumerate(panels, 2):
        cells.append(markdown(f"## {panel['title']}\n\n{panel['description']}\n\n**Method:** {panel['method']}\n"))
        encoded = base64.b64encode(panel["png"].read_bytes()).decode("ascii")
        cells.append({"cell_type": "code", "execution_count": i, "metadata": {},
            "source": [f"display(Image(filename=str(ROOT / 'reports/figures/initial_{panel['slug']}.png')))\n"],
            "outputs": [{"output_type": "display_data", "metadata": {},
                         "data": {"image/png": encoded, "text/plain": [f"Initial analysis: {panel['slug']}"]}}]})
    cells.append(markdown("## Sources and scope\n\nETF: [Pinned mirror](https://github.com/manisahni/marketdata/tree/65a079329e379e104495f459e12e76a8f995585a), VIX and rates: [FRED](https://fred.stlouisfed.org/series/VIXCLS). Source hashes are recorded in `data/raw/sources.json` . This analysis is descriptive and does not establish strategy alpha or causality.\n"))
    notebook = {"nbformat": 4, "nbformat_minor": 5, "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.9"}}, "cells": cells}
    for i, cell in enumerate(cells):
        cell["id"] = f"initial-{i:02d}"
    folder = ROOT / "notebooks"
    folder.mkdir(exist_ok=True)
    (folder / "initial_analysis.ipynb").write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
