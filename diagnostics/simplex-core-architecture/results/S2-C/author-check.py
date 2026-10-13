from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/S2-C';B=D.parent/'S2-B'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pins=json.loads((D/'pins.json').read_text()); old=json.loads((B/'source-check.json').read_text()); closure=json.loads((B/'closure.json').read_text())
checks={'full535_hashes':len(pins)==535 and all(sha(Path(p))==h for p,h in pins.items()),'all_B_closure24':len(closure['sha256'])==24 and all(sha(Path(p))==h for p,h in closure['sha256'].items()),'B_source_pins':all(old['sha256'][str(R/p)]==sha(R/p) for p in old['source_comparisons']),'source21':all(json.loads((D/'source-check.json').read_text())['checks'].values()),'refs':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()=='dee5b167c54daaaa1c2273729278da2a86c7880d' and subprocess.check_output(['git','rev-parse','master'],text=True).strip()=='d02416c108f06fcd41d58e0a1980b70a51fef9ef','no_tracked_edits':not subprocess.check_output(['git','diff','--name-only'],text=True).strip()}
extra=[D/'source-check.json',D/'pins.json',D/'author-check.py',R/'diagnostics/simplex-core-architecture/S2-PRICE-AUDIT-VALUES-PREPARATION.md',R/'docs/superpowers/plans/2026-10-13-price-audit-values-admission.md']
with (D/'author-check.json').open('x') as f:json.dump({'checks':checks,'all_passed':all(checks.values()),'sha256':{str(p):sha(p) for p in extra}},f,indent=2);f.write('\n')
print(checks);assert all(checks.values())
