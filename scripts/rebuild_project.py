"""Verify the saved data, rebuild all reports, run checks, and assemble the final report."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.matplotlib'))
OUT=ROOT/'reports';OUT.mkdir(exist_ok=True)
old_path=OUT/'backtest_v1_summary.json'
before=json.loads(old_path.read_text()) if old_path.exists() else None

def build(script):
    result=subprocess.run([sys.executable,str(ROOT/'scripts'/script)],text=True,capture_output=True)
    if result.returncode:
        print(result.stdout);print(result.stderr,file=sys.stderr)
        raise SystemExit(result.returncode)
    print('PASS:',script)

build('download_data.py')
for script in ('primary_analysis.py','backtest_strategy_v1.py','build_initial_analysis.py','build_backtest_report.py','analyze_performance.py'):
    build(script)
suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
check=unittest.TextTestRunner(verbosity=1).run(suite)
if not check.wasSuccessful():raise SystemExit(1)
after=json.loads(old_path.read_text())
manifest=json.loads((ROOT/'data/raw/sources.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(ROOT/manifest['processed']['path'])==manifest['processed']['sha256']
for name,record in manifest['files'].items():
    assert sha(ROOT/'data/raw'/name)==record['sha256']
review={'status':'passed','review_date':'2026-10-22','unit_tests':check.testsRun,
        'backtest_metrics_unchanged':before==after if before is not None else None,
        'processed_sha256':manifest['processed']['sha256'],
        'verified_raw_files':len(manifest['files']),
        'checks':['signal/execution timing','historical-prefix invariance','exact self-financing charges','daily and period P&L reconciliation','buy-and-hold closed form','monthly rebalance schedule','snapshot-drift rejection','invalid-input rejection'],
        'limitations':['secondary ETF history not fully cross-validated','adjusted-close execution approximation','no additional execution-delay test','post-test benchmark selection','current FRED history, not a vintage archive'],
        'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'scripts').glob('*.py'))}}
(OUT/'review_checks.json').write_text(json.dumps(review,indent=2)+'\n')
build('build_final_report.py')
print(f"Complete: {check.testsRun} tests passed; prior backtest metrics unchanged={review['backtest_metrics_unchanged']}")
