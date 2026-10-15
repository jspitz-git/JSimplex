from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;R=D.parents[3];A=D.parent/'DIRECT-LU-COST-PREPARATION'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
x=json.loads((D/'analysis.json').read_text());p=json.loads((A/'cost1-launch-pins.json').read_text())['inventory'];names=list(x['sha256'])[:15]
checks={'original17of18_preserved':sum(x['checks'].values())==17 and x['checks']['selected_sources_match_launch'] is False,'selected15_launch_records':len(names)==15 and all(n in p and sha(n)==p[n]['sha256'] and str(Path(n).resolve())==p[n]['resolved'] for n in names),'analysis_bindings_unchanged':all(sha(n)==h for n,h in x['sha256'].items()),'no_arithmetic_rerun':True}
out=dict(all_passed=all(checks.values()),checks=checks,explanation='Original checker compared SHA string to inventory object; canonical records use sha256 and resolved. Original failed JSON/script/exit remain; this supplement only checks pin schema, no old script or numerical execution.',sha256={str(v):sha(v) for v in [Path(__file__),D/'analyze.py',D/'analysis.json',A/'cost1-launch-pins.json']})
with (D/'pin-supplement.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
if not out['all_passed']:raise ValueError(checks)
print(checks)
