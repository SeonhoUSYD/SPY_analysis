"""Reproduce a verified snapshot; refresh mutable FRED sources only on request."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
from datetime import datetime, timezone
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


def download(url: str) -> bytes:
    result = subprocess.run(
        ["curl", "--http1.1", "--fail", "--location", "--silent", "--show-error",
         "--max-time", "60", "--retry", "2", url],
        check=True, capture_output=True,
    )
    data = result.stdout
    if not data or b"<html" in data[:200].lower():
        raise ValueError(f"Unexpected download response: {url}")
    return data


def load_fred(data: bytes, column: str) -> dict[str, float]:
    values = {}
    with io.StringIO(data.decode("utf-8-sig"), newline="") as stream:
        for row in csv.DictReader(stream):
            day = row["observation_date"]
            if day in values:
                raise ValueError(f"Duplicate {column} date: {day}")
            value = row[column].strip()
            if value and value != ".":
                number = float(value)
                if not math.isfinite(number):
                    raise ValueError(f"Nonfinite {column} value on {day}")
                values[day] = number
    return values


def build_dataset(snapshots: dict[str, bytes]) -> tuple[bytes, dict]:
    vix = load_fred(snapshots["fred_vixcls.csv"], "VIXCLS")
    rate = load_fred(snapshots["fred_dgs3mo.csv"], "DGS3MO")
    fields = [
        "date", "spy_adj_close", "tlt_adj_close", "gld_adj_close",
        "vix_close", "dgs3mo_pct", "vix_lag1", "dgs3mo_lag1",
    ]
    rows = []
    prev_vix = None
    prev_rate = None
    seen = set()
    with io.StringIO(snapshots["etf_adjusted_close_snapshot.csv"].decode("utf-8-sig"), newline="") as stream:
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
            if any(not math.isfinite(p) or p <= 0 for p in prices):
                raise ValueError(f"Nonfinite or nonpositive price on {day}")
            current_vix = vix.get(day)
            current_rate = rate.get(day)
            if current_vix is not None and current_vix <= 0:
                raise ValueError(f"Nonpositive VIX on {day}")
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
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    output_bytes = stream.getvalue().encode("utf-8")
    processed = {
        "path": "data/processed/market_daily.csv",
        "rows": len(rows),
        "first_date": rows[0]["date"],
        "last_date": rows[-1]["date"],
        "missing_vix": sum(row["vix_close"] == "" for row in rows),
        "missing_rate": sum(row["dgs3mo_pct"] == "" for row in rows),
        "sha256": hashlib.sha256(output_bytes).hexdigest(),
    }
    return output_bytes, processed


def verify_hash(data: bytes, expected: str, label: str) -> None:
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(
            f"Snapshot hash mismatch: {label}. Existing research files were not overwritten. "
            "Restore the recorded snapshot to reproduce the published analysis. "
            "Use --refresh only to deliberately adopt a new data snapshot, then rebuild "
            "and review all results; mutable FRED downloads may differ from the original."
        )


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh", action="store_true",
        help="Explicitly redownload sources and replace the manifest; FRED history can change.",
    )
    args = parser.parse_args(argv)
    manifest_path = RAW / "sources.json"
    if args.refresh:
        manifest = {
            "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
            "period": [START, END],
            "etf_source_repository": "https://github.com/manisahni/marketdata",
            "etf_source_commit": COMMIT,
            "etf_source_claim": "Yahoo Finance auto_adjust=True cache; secondary mirror",
            "fred_snapshot_note": (
                "Explicit refresh of mutable FRED endpoints, not a point-in-time vintage. "
                "The pinned ETF mirror commit is unchanged."
            ),
            "files": {},
        }
    else:
        if not manifest_path.exists():
            raise ValueError("No source manifest. Restore sources.json or use --refresh to create a new snapshot.")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["etf_source_commit"] != COMMIT or manifest["period"] != [START, END]:
            raise ValueError("Manifest source or period differs from this script. Restore matching code or use --refresh.")

    # Stage every source and validate the derived dataset before writing any research file.
    snapshots = {}
    for filename, url in SOURCES.items():
        path = RAW / filename
        data = path.read_bytes() if path.exists() and not args.refresh else download(url)
        if args.refresh:
            manifest["files"][filename] = {
                "url": url, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            }
        else:
            verify_hash(data, manifest["files"][filename]["sha256"], filename)
        snapshots[filename] = data
    output_bytes, processed = build_dataset(snapshots)
    output = PROCESSED / "market_daily.csv"
    if not args.refresh:
        verify_hash(output_bytes, manifest["processed"]["sha256"], "rebuilt market_daily.csv")
        if output.exists():
            verify_hash(output.read_bytes(), manifest["processed"]["sha256"], "local market_daily.csv")

    RAW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    for filename, data in snapshots.items():
        path = RAW / filename
        if args.refresh or not path.exists():
            path.write_bytes(data)
    if args.refresh or not output.exists():
        output.write_bytes(output_bytes)
    if args.refresh:
        manifest["processed"] = processed
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Refreshed snapshot." if args.refresh else "Verified recorded snapshot; existing files preserved.")
    print(json.dumps(manifest["processed"], indent=2))


if __name__ == "__main__":
    main()
