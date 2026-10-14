from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent
old=(D.with_name('MA-S-LOAD')/'driver.jl').read_text()
checks={n:s not in old for n,s in {'new_candidate':'../MA-U','durable_window':'whole-metrics','complete_record':'whole-complete','setup_interval':'bundle_snapshot_setup_seconds','runtime_refusal':'VERSION == v"1.13.0"'}.items()}
with (D/'preparation-red.json').open('x') as f:json.dump(dict(all_expected_missing=all(checks.values()),checks=checks,scope='Source structural RED only; no Julia or old driver execution',sha256={str(D/'preparation-red.py'):hashlib.sha256((D/'preparation-red.py').read_bytes()).hexdigest()}),f,indent=2)
if not all(checks.values()):raise SystemExit(1)
print('five expected missing admission features')
