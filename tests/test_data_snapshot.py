"""Snapshot drift must fail before cached research data are overwritten."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import download_data as source
import backtest_strategy_v1 as engine

class SnapshotTests(unittest.TestCase):
    def test_corrupt_cache_is_rejected_without_network_or_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp)/'raw'; raw.mkdir()
            processed = Path(tmp)/'processed'
            manifest={'etf_source_commit':source.COMMIT,'period':[source.START,source.END],
                      'files':{'etf_adjusted_close_snapshot.csv':{'sha256':hashlib.sha256(b'original').hexdigest()}}}
            m=raw/'sources.json'; original=json.dumps(manifest);m.write_text(original)
            cache=raw/'etf_adjusted_close_snapshot.csv';cache.write_bytes(b'changed')
            with patch.object(source,'RAW',raw),patch.object(source,'PROCESSED',processed),patch.object(source,'download') as network:
                with self.assertRaisesRegex(ValueError,'Snapshot hash mismatch'):
                    source.main([])
                network.assert_not_called()
            self.assertEqual(m.read_text(),original)
            self.assertEqual(cache.read_bytes(),b'changed')
            self.assertFalse(processed.exists())

    def test_missing_cache_download_must_match_manifest_before_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw=Path(tmp)/'raw';raw.mkdir()
            manifest={'etf_source_commit':source.COMMIT,'period':[source.START,source.END],
                      'files':{'etf_adjusted_close_snapshot.csv':{'sha256':hashlib.sha256(b'original').hexdigest()}}}
            (raw/'sources.json').write_text(json.dumps(manifest))
            with patch.object(source,'RAW',raw),patch.object(source,'PROCESSED',Path(tmp)/'processed'),patch.object(source,'download',return_value=b'drifted'):
                with self.assertRaisesRegex(ValueError,'Snapshot hash mismatch'):
                    source.main([])
            self.assertFalse((raw/'etf_adjusted_close_snapshot.csv').exists())

    def test_bad_inputs_are_explicit_errors(self):
        for mode,cost in [('unknown',0.0),('spy',float('nan')),('spy',-.001)]:
            with self.assertRaises(ValueError):
                engine.run([],0,mode,cost)
        with self.assertRaises(ValueError):
            engine.signal([],0)
        with self.assertRaisesRegex(ValueError,'Nonfinite'):
            source.load_fred(b'observation_date,VIXCLS\n2020-01-01,nan\n','VIXCLS')

if __name__=='__main__': unittest.main()
