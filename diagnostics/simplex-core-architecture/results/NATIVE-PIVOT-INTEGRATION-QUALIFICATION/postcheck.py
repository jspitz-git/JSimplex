"""One-shot post-exit evidence collector, never executes numerical/auditor code."""
from pathlib import Path
import sys,json,hashlib,tomllib
K=Path(__file__).resolve().parent;R=K.parents[3];E=K.parent/'NATIVE-PIVOT-INTEGRATION-ENVIRONMENT-AMENDMENT'
sys.path.insert(0,str(E));from control import *
run=E/'runs/integration';out=run/'output';record={};checks={}
def digest(p):return sha(p)
h=full_host(rd(run/'posthost.json')['groups']);save(K/'post-exit-host.json',h)
checks['fresh_no_processes']=not h['matches'];checks['refs_boot']=all(h[x]==rd(run/'host.json')[x] for x in ['head','master','boot_id'])
checks['launch_pins']=all(digest(Path(n))==z['sha256'] and str(Path(n).resolve())==z['resolved'] for n,z in rd(run/'launch-pins.json')['inventory'].items())
checks['admission']=bindings(rd(run/'admission.json'))
checks['output_pins_equal']=rd(out/'pins.json')==rd(run/'launch-pins.json')
p=rd(out/'process.json');inv=rd(run/'invocation.json');audit=rd(run/'audit.json')
checks['recorded_process_closure']=all(p[role][x] in h['groups'] for role in ['runner','child'] for x in ['pgid','sid'])
checks['audit_bindings']=bindings(audit)
checks['raw_preserved']=(out/'raw.toml').is_file()
checks['actual520']=all(sha(R/n)==s for n,s in rd(E/'actual-baseline.json')['sha256'].items())
checks['before_texts']=sha(STATUS)==sha(K/'STATUS.md.before-integration-run') and sha(ROAD)==sha(K/'roadmap.md.before-integration-run')
record.update(process=p,invocation=inv,audit_passed=audit['all_passed'],audit_error=audit.get('error'),selected_result=audit.get('result'),out_files=sorted(x.name for x in out.iterdir()),scope='Preservation/integrity separately from numerical acceptance; no auditor rerun')
if (out/'raw.toml').is_file():
 try:record['raw_summary']=tomllib.loads((out/'raw.toml').read_text())
 except Exception as exc:record['raw_parse_error']=repr(exc)
save(K/'postcheck.json',dict(all_passed=all(checks.values()),checks=checks,record=record,sha256={str(p):sha(p) for p in [run/'audit.json',run/'admission.json',run/'invocation.json',out/'process.json',K/'post-exit-host.json',K/'postcheck.py']}))
require(all(checks.values()),'Postcheck integrity failed; preserve');print(dict(checks=len(checks),audit_passed=audit['all_passed'],returncode=p['returncode'],inclusive_seconds=inv['elapsed_seconds'],groups=len(h['groups'])))
