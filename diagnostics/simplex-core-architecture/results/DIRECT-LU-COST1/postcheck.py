"""New supplemental post-run inspection; no old audit/launcher execution."""
from pathlib import Path
import sys,json,tomllib,hashlib,subprocess
D=Path(__file__).resolve().parent;A=D.parent/'DIRECT-LU-COST-PREPARATION';R=D.parents[3]
sys.path.insert(0,str(A))
from control import sha,rd,save,host,req,validate_review
import guard
phase='cost1';out=A/'cost1-run';inv=rd(A/'cost1-invocation.json');process=rd(out/'process.json');audit=rd(A/'cost1-audit.json');sealed=rd(A/'cost1-sealed-pins.json');pins=rd(A/'cost1-launch-pins.json')
validate_review(rd(A/'cost1-admission.json'),A/'cost1-sealed-pins.json',sealed['files']+[str(A/'cost1-sealed-pins.json')])
raw=tomllib.loads((out/'raw.toml').read_text()) if (out/'raw.toml').exists() else None
rows=[];parse_errors=[]
for p in sorted(out.glob('window-*.toml')):
 try:rows.append(dict(path=p.name,row=tomllib.loads(p.read_text())))
 except Exception as e:parse_errors.append(dict(path=p.name,error=repr(e)))
resources=[json.loads(s) for s in (out/'resources.jsonl').read_text().splitlines()]+[process['terminal_memory']]
previous=rd(A/'cost1-posthost.json');fresh=host(previous['groups']);save(D/'final-host.json',fresh)
base=rd(D.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256']
checks=dict(stage_review=True,launch_pins=guard.pins_match(pins),sealed_pins=guard.pins_match(sealed),
 raw_pins=rd(out/'pins.json')==pins,audit_bindings=all(sha(n)==h for n,h in audit['sha256'].items()),
 prior_groups_and_new_sessions=not fresh['matches'] and set(fresh['groups'])==set(previous['groups']),
 refs_boot=all(fresh[k]==sealed[k] for k in ('head','master','boot_id')),
 baseline514=len(base)==514 and all(sha(R/n)==h for n,h in base.items()),
 bounded=inv['elapsed_seconds']<=90 and inv['supervisor']['elapsed_seconds']<=90,
 resources=all(s['available_kib']>=6*1024**2 and s['swap_used_kib']<=1024**2 for s in resources),
 no_cost2=not any(A.glob('cost2-*')))
paths=[p for p in A.glob('cost1-*') if p.is_file()]+[p for p in out.rglob('*') if p.is_file()]+[D/'postcheck.py',D/'final-host.json']
summary=dict(raw=raw,canonical_audit_pass=audit['all_passed'],canonical_checks=audit['checks'],audit_error=audit['error'],returncode=process['returncode'],reason=process['reason'],inclusive_seconds=inv['elapsed_seconds'],supervisor=inv['supervisor'],windows_written=len(rows),window_parse_errors=parse_errors,cell_files=len(list(out.glob('cell-*.toml'))),started_files=len(list(out.glob('started-*.toml'))),measured_windows=sum(x['row'].get('measured') is True for x in rows),correct_windows=sum(x['row'].get('correct') is True for x in rows),measured_compile_failures=sum(x['row'].get('measured') is True and (x['row'].get('compile_seconds')!=0 or x['row'].get('recompile_seconds')!=0) for x in rows),min_available_kib=min(s['available_kib'] for s in resources),max_swap_kib=max(s['swap_used_kib'] for s in resources),resource_records=len(resources)-1,groups=len(fresh['groups']))
save(D/'postcheck.json',dict(all_passed=all(checks.values()),checks=checks,summary=summary,sha256={str(p):sha(p) for p in sorted(paths)}))
print(json.dumps(dict(checks=checks,summary=summary),indent=2));req(all(checks.values()),'Supplemental integrity checks failed')
