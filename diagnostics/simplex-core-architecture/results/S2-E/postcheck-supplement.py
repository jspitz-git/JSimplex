"""Correct only supplemental author file-count expectations; never rerun the auditor."""
from pathlib import Path
import json,hashlib
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/S2-E';D=E.parent/'S2-D';O=R/'.superpowers/simplex-core-architecture/S2-D/qualification-1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
a=json.loads((E/'postcheck.json').read_text());audit=json.loads((D/'audit.json').read_text());pairs=a['raw_pairs']
false={k for k,v in a['checks'].items() if not v};expected={'current.json','pins.json','process.json','resources.jsonl','run.log','raw/regression.toml','raw/complete.toml'}|{'raw/'+t+'-'+s+'-'+str(m)+'.toml' for t in ['Float32','Float64'] for s in ['sparse','dense'] for m in [32,128]}
checks={'original_two_count_failures_preserved':a['all_passed'] is False and false=={'raw16_portable_byteidentical','audit_raw16_bindings'},'exact15_names':len(expected)==15 and {str(Path(p).relative_to(O)) for p in pairs}==expected,'all15_original_portable_bytes':len(pairs)==15 and all(Path(p).read_bytes()==Path(v['portable']).read_bytes() and sha(p)==v['sha256']==v['portable_sha256'] for p,v in pairs.items()),'audit15_exact_bindings':set(audit['raw_sha256'])==set(pairs) and all(sha(p)==h for p,h in audit['raw_sha256'].items()),'other12_checks_recorded_pass':len(a['checks'])==14 and all(v for k,v in a['checks'].items() if k not in false),'original_audit21_pass':audit['all_passed'] is True and len(audit['checks'])==21 and all(audit['checks'].values())}
paths=[E/'postcheck.py',E/'postcheck.json',E/'cost-summary.json',E/'postcheck-supplement.py',D/'audit.json']
o={'checks':checks,'all_passed':all(checks.values()),'explanation':'10 Julia raw files plus five process/pins/resource/log files =15, not16. Original 12/14 supplemental author record and exit1 preserved; no numerical/auditor rerun. All byte comparisons pass.','sha256':{str(p):sha(p) for p in paths}}
with (E/'postcheck-supplement.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps(o))
if not o['all_passed']:raise SystemExit(1)
