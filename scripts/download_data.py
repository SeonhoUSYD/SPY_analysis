"""Download pinned ETF closes and FRED series; build a local daily dataset."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
COMMIT = "65a079329e379e104495f459e12e76a8f995585a"
SOURCES = {
    "etf_adjusted_close_snapshot.csv": (
        f"https://raw.githubusercontent.com/manisahni/marketdata/{COMMIT}/daily_adjclose.csv"
    ),
    "fred_vixcls.csv": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS",
    "fred_dgs3mo.csv": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS3MO",
}
START = "2007-01-01"
END = "2025-12-31"


def download(url: str, path: Path) -> bytes:
    result = subprocess.run(
        ["curl", "--http1.1", "--fail", "--location", "--silent", "--show-error",
         "--max-time", "60", "--retry", "2", url],
        check=True, capture_output=True,
    )
    data = result.stdout
    if not data or b"<html" in data[:200].lower():
        raise ValueError(f"Unexpected download response: {url}")
    path.write_bytes(data)
    return data


def load_fred(path: Path, column: str) -> dict[str, float]:
    values = {}
    with path.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            value = row[column].strip()
            if value and value != ".":
                values[row["observation_date"]] = float(value)
    return values


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    manifest = {
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "period": [START, END],
        "etf_source_repository": "https://github.com/manisahni/marketdata",
        "etf_source_commit": COMMIT,
        "etf_source_claim": "Yahoo Finance auto_adjust=True cache; secondary mirror",
        "files": {},
    }
    for filename, url in SOURCES.items():
        path = RAW / filename
        data = download(url, path)
        manifest["files"][filename] = {
            "url": url,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }

    vix = load_fred(RAW / "fred_vixcls.csv", "VIXCLS")
    rate = load_fred(RAW / "fred_dgs3mo.csv", "DGS3MO")
    fields = [
        "date", "spy_adj_close", "tlt_adj_close", "gld_adj_close",
        "vix_close", "dgs3mo_pct", "vix_lag1", "dgs3mo_lag1",
    ]
    output = PROCESSED / "market_daily.csv"
    rows = []
    prev_vix = None
    prev_rate = None
    seen = set()
    with (RAW / "etf_adjusted_close_snapshot.csv").open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            day = row["Date"]
            if day < START or day > END:
                continue
            if day in seen:
                raise ValueError(f"Duplicate ETF date: {day}")
            seen.add(day)
            if not all(row[symbol].strip() for symbol in ("SPY", "TLT", "GLD")):
                continue
            prices = [float(row[symbol]) for symbol in ("SPY", "TLT", "GLD")]
            if any(p <= 0 for p in prices):
                raise ValueError(f"Nonpositive price on {day}")
            current_vix = vix.get(day)
            current_rate = rate.get(day)
            rows.append({
                "date": day,
                "spy_adj_close": prices[0],
                "tlt_adj_close": prices[1],
                "gld_adj_close": prices[2],
                "vix_close": "" if current_vix is None else current_vix,
                "dgs3mo_pct": "" if current_rate is None else current_rate,
                "vix_lag1": "" if prev_vix is None else prev_vix,
                "dgs3mo_lag1": "" if prev_rate is None else prev_rate,
            })
            if current_vix is not None:
                prev_vix = current_vix
            if current_rate is not None:
                prev_rate = current_rate
    if len(rows) < 4000 or rows != sorted(rows, key=lambda row: row["date"]):
        raise ValueError("Unexpected date coverage or ordering")
    if not any(row["date"] == "2025-12-31" for row in rows):
        raise ValueError("Dataset does not reach 2025-12-31")
    by_date = {row["date"]: row for row in rows}
    if abs(float(by_date["2020-03-16"]["vix_close"]) - 82.69) > 1e-6:
        raise ValueError("VIX historical anchor did not match FRED")
    if abs(float(by_date["2025-12-31"]["gld_adj_close"]) - 396.31) > 0.01:
        raise ValueError("GLD historical anchor did not match Nasdaq close")
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    manifest["processed"] = {
        "path": str(output.relative_to(ROOT)),
        "rows": len(rows),
        "first_date": rows[0]["date"],
        "last_date": rows[-1]["date"],
        "missing_vix": sum(row["vix_close"] == "" for row in rows),
        "missing_rate": sum(row["dgs3mo_pct"] == "" for row in rows),
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    }
    (RAW / "sources.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest["processed"], indent=2))


if __name__ == "__main__":
    main()
