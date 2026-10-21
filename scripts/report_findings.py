"""Narrative values computed from the same objects as report tables."""

def backtest_findings(results):
    def get(name, bps):
        return next(r for r in results if r['period'] == 'Final test' and r['strategy'] == name and r['bps'] == bps)
    v, s = get('Strategy v1', 5), get('SPY buy-and-hold', 5)
    v20, s20 = get('Strategy v1', 20), get('SPY buy-and-hold', 20)
    return (f"At 5 bp per traded dollar, v1 returned {v['cagr']:.2%} annualized versus {s['cagr']:.2%} for SPY, "
            f"with maximum drawdowns of {v['max_drawdown']:.2%} and {s['max_drawdown']:.2%}. "
            f"Annualized volatility was {v['volatility']:.2%} versus {s['volatility']:.2%}. "
            f"At 20 bp, the respective annualized returns were {v20['cagr']:.2%} and {s20['cagr']:.2%}. "
            "These are historical comparisons; execution and data assumptions affect their interpretation.")


def performance_findings(summary, attribution, sensitivity):
    by_name = {r['strategy']: r for r in summary}
    v = by_name['Strategy v1']
    f = by_name['Monthly SPY 40% / cash 60%']
    g = by_name['Monthly SPY 40 / GLD 30 / cash 30']
    b = by_name['Monthly SPY 40 / TLT 20 / GLD 20 / cash 20']
    d = by_name['VIX equity rule / cash only']
    def attr(period, name='Strategy v1'):
        return next(r for r in attribution if r['period'] == period and r['strategy'] == name)
    total, y20, y22 = attr('2018–2025'), attr('2020'), attr('2022')
    w20 = next(r for r in attribution if r['period'].startswith('2020 v1 drawdown') and r['strategy']=='Strategy v1')
    w22 = next(r for r in attribution if r['period'].startswith('2022 v1 drawdown') and r['strategy']=='Strategy v1')
    c20 = {r['strategy']:r for r in sensitivity if r['bps']==20}
    return [
        f"V1 and the monthly 40% SPY benchmark have mean equity weights of {v['mean_spy_weight']:.2%} and {f['mean_spy_weight']:.2%}. "
        f"Their annualized returns are {v['cagr']:.2%} and {f['cagr']:.2%}, volatility {v['volatility']:.2%} and {f['volatility']:.2%}, "
        f"and maximum drawdowns {v['max_drawdown']:.2%} and {f['max_drawdown']:.2%}. "
        "The fixed benchmark provides a direct check on how much drawdown reduction is available from lower equity exposure alone. It is not a causal decomposition of v1.",
        f"GLD contributed {total['GLD']*100:+.2f} percentage points to v1's {total['return']:+.2%} cumulative net return; "
        f"SPY contributed {total['SPY']*100:+.2f} points, TLT {total['TLT']*100:+.2f}, cash {total['Cash']*100:+.2f}, "
        f"and charges {total['Costs']*100:+.2f}. These contributions add to the cumulative return, not CAGR. "
        f"The cash-only VIX variant returned {d['cagr']:.2%} annualized with a {d['max_drawdown']:.2%} maximum drawdown.",
        f"In 2020, v1's calendar return was {y20['return']:+.2%}, including {y20['GLD']*100:+.2f} points from GLD. "
        f"In 2022, v1 returned {y22['return']:+.2%}, versus {attr('2022', f['strategy'])['return']:+.2%} for the fixed equity/cash benchmark. "
        f"During the retrospectively selected {w20['period']}, TLT and GLD contributed {w20['TLT']*100:+.2f} and {w20['GLD']*100:+.2f} points. "
        f"During the {w22['period']}, GLD contributed {w22['GLD']*100:+.2f} points. Full-year returns include recoveries and should not be used to describe peak-to-trough protection.",
        f"At 5 bp, the SPY/GLD/cash static portfolio returned {g['cagr']:.2%} annualized with {g['volatility']:.2%} volatility and a {g['max_drawdown']:.2%} maximum drawdown. "
        f"The four-asset static portfolio returned {b['cagr']:.2%}, with {b['volatility']:.2%} volatility and a {b['max_drawdown']:.2%} drawdown. "
        f"At 20 bp, v1 returned {c20[v['strategy']]['cagr']:.2%} versus {c20[g['strategy']]['cagr']:.2%} for SPY/GLD/cash, "
        f"a gap of {(c20[v['strategy']]['cagr']-c20[g['strategy']]['cagr'])*100:.2f} percentage points. "
        "The weights were documented before these benchmark runs, after the original final-test results had been observed. No weight search was performed; this remains a retrospective comparison."
    ]
