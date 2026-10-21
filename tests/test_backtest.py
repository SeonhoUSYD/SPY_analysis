"""Independent accounting and execution checks using deterministic synthetic data.

Run from the repository root: python3 -m unittest discover -s tests -v
No downloaded market data or third-party packages are required.
"""

import math
from pathlib import Path
import sys
import unittest
from datetime import date, timedelta
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import backtest_strategy_v1 as engine


def market_rows(count=400):
    """Business-day observations with varying prices and fully observed inputs."""
    rows = []
    day = date(2020, 1, 6)
    prices = [100.0, 100.0, 100.0]
    while len(rows) < count:
        if day.weekday() < 5:
            i = len(rows)
            returns = (
                0.0002 + 0.004 * math.sin(i * 0.37),
                0.0001 + 0.003 * math.cos(i * 0.23),
                0.00015 + 0.005 * math.sin(i * 0.11),
            )
            prices = [p * (1 + r) for p, r in zip(prices, returns)]
            rows.append({
                "date": day.isoformat(), "day": day,
                **dict(zip(engine.ASSETS, prices)),
                "vix": 18 + 6 * math.sin(i * 0.19),
                "cash_rate": 0.03 / 252,
            })
        day += timedelta(days=1)
    return rows


class BacktestAccountingTests(unittest.TestCase):
    start = 253

    def test_friday_signal_executes_after_next_session_return(self):
        rows = market_rows(257)
        for row in rows:
            row.update(spy=100.0, tlt=100.0, gld=100.0, cash_rate=0.0)
        self.assertEqual(rows[254]["day"].weekday(), 4)
        self.assertEqual(rows[255]["day"].weekday(), 0)
        rows[255]["spy"] = 200.0
        rows[256]["spy"] = 400.0

        def chosen_signal(_rows, t):
            equity = 0.15 if t == 254 else 0.40
            return [equity, 0.0, 0.0, 1 - equity], "high", (False, False)

        with patch.object(engine, "signal", side_effect=chosen_signal):
            result = engine.run(rows, self.start, "v1", 0.0)
        # Thursday starts at 40%. Friday's signal cannot earn Monday's jump
        # with its new 15% exposure; that allocation only earns Tuesday's jump.
        for actual, expected in zip(result["values"], [1.0, 1.0, 1.4, 1.61]):
            self.assertAlmostEqual(actual, expected, places=12)
        self.assertAlmostEqual(result["weights"][1][0], 0.40)
        self.assertAlmostEqual(result["weights"][2][0], 0.15)
        self.assertEqual(result["trades"], 2)

    def test_appended_future_does_not_change_history(self):
        rows = market_rows()
        prefix_length = 333
        for mode in ("v1", "spy", "equal", "fixed40", "dynamic_cash", "gold_cash", "balanced40"):
            with self.subTest(mode=mode):
                prefix = engine.run(rows[:prefix_length], self.start, mode, 0.0005)
                full = engine.run(rows, self.start, mode, 0.0005)
                n = prefix_length - self.start
                for key in ("values", "weights", "pnl", "costs"):
                    self.assertEqual(prefix[key], full[key][:n])
        for t in (252, 300, 332):
            self.assertEqual(engine.signal(rows, t), engine.signal(rows[:t + 1], t))

    def test_buy_and_hold_matches_closed_form_including_purchase_cost(self):
        rows = market_rows(290)
        for rate in (0.0, 0.0005, 0.002):
            with self.subTest(rate=rate):
                result = engine.run(rows, self.start, "spy", rate)
                # Buying X dollars of ETF costs rate * X, so X = 1/(1+rate).
                initial_holding = 1 / (1 + rate)
                for row, actual in zip(rows[self.start:], result["values"]):
                    expected = initial_holding * row["spy"] / rows[self.start]["spy"]
                    self.assertAlmostEqual(actual, expected, places=12)
                self.assertAlmostEqual(result["costs"][0], rate / (1 + rate), places=12)
                self.assertTrue(all(cost == 0 for cost in result["costs"][1:]))
                self.assertEqual(result["trades"], 1)

    def test_self_financing_costs_and_daily_attribution(self):
        rows = market_rows()
        rate = 0.002
        for mode in ("v1", "equal", "fixed40", "dynamic_cash", "gold_cash", "balanced40"):
            with self.subTest(mode=mode):
                result = engine.run(rows, self.start, mode, rate)
                previous_value = 1.0
                previous_holdings = [0.0, 0.0, 0.0, 1.0]
                for i, (value, weights, pnl, cost) in enumerate(zip(
                    result["values"], result["weights"], result["pnl"], result["costs"]
                )):
                    t = self.start + i
                    relatives = [1.0] * 4 if i == 0 else [
                        rows[t][asset] / rows[t - 1][asset] for asset in engine.ASSETS
                    ] + [1 + rows[t - 1]["cash_rate"]]
                    before_trade = [amount * relative for amount, relative in zip(previous_holdings, relatives)]
                    after_trade = [value * weight for weight in weights]
                    traded_dollars = sum(abs(after_trade[j] - before_trade[j]) for j in range(3))
                    self.assertAlmostEqual(cost, rate * traded_dollars, places=11)
                    self.assertAlmostEqual(value + cost, sum(before_trade), places=11)
                    self.assertAlmostEqual(value - previous_value, sum(pnl) - cost, places=11)
                    self.assertAlmostEqual(sum(weights), 1.0, places=12)
                    self.assertGreaterEqual(min(weights), 0.0)
                    previous_value, previous_holdings = value, after_trade

    def test_static_portfolio_rebalances_on_first_session_of_month(self):
        rows = market_rows(350)
        result = engine.run(rows, self.start, "gold_cash", 0.0005)
        expected_events = 0
        for i, t in enumerate(range(self.start, len(rows))):
            is_rebalance = t == self.start or rows[t]["date"][:7] != rows[t - 1]["date"][:7]
            if is_rebalance:
                expected_events += 1
                self.assertEqual(result["weights"][i], [0.4, 0.0, 0.3, 0.3])
                self.assertGreater(result["costs"][i], 0)
            else:
                self.assertEqual(result["costs"][i], 0)
        self.assertEqual(result["trades"], expected_events)


if __name__ == "__main__":
    unittest.main()
