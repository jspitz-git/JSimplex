from pathlib import Path
import json,tomllib,hashlib
D=Path(__file__).resolve().parent
raw=tomllib.loads((D/'run-1/raw.toml').read_text());pins=json.loads((D/'pins-reviewed.json').read_text());bound={x['resolved'] for x in pins['inventory'].values()}
missing={k:v for k,v in raw['loaded_paths'].items() if str(Path(v).resolve()) not in bound}
checks={'exact_missing_modules':{Path(v).stem for v in missing.values()}=={'FileWatching','Sockets'} and len(missing)==2,'original_false_preserved':json.loads((D/'failure-analysis.json').read_text())['checks']['loaded_module_paths_pinned'] is False,'all_other_analysis_checks_pass':all(v for k,v in json.loads((D/'failure-analysis.json').read_text())['checks'].items() if k!='loaded_module_paths_pinned'),'no_retroactive_launch_membership':all(str(Path(v)) not in pins['inventory'] for v in missing.values())}
record=dict(all_passed=all(checks.values()),checks=checks,missing_loaded_module_entries=missing,scope='Source entries observed in raw runtime list but NOT launch-bound. New read-time hashes below are not retroactive pins. Full loaded-path gate remains FALSE; qualification NOT ACCEPTED.',sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(v) for v in missing.values()]+[D/'failure-analysis.json',D/'run-1/raw.toml',D/'pins-reviewed.json',Path(__file__)]})
with (D/'loaded-path-supplement.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(checks)
if not record['all_passed']:raise ValueError('supplement failed')
