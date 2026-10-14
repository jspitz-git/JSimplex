"""New post-execution reconciliation only; not a launch pin or numerical rerun."""
from pathlib import Path
import hashlib,json,subprocess,tomllib
R=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent;A=D.parent/'DIRECT-LU-ADMISSION'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def check_pins(p):
    paths={Path(n) for n in p['files']}
    for t in p['trees']:paths.update(q for q in Path(t).rglob('*') if q.is_file())
    return {str(q):dict(resolved=str(q.resolve(strict=True)),sha256=sha(q)) for q in sorted(paths)}==p['inventory']
checks={};results={};bindings={}
for phase in ('red','green'):
    out=A/(phase+'-run');ap=A/(phase+'-audit.json')
    if not ap.exists():
        checks[phase+'_executed_and_audited']=False;continue
    audit=rd(ap);cfg=rd(A/'config.json')['phases'][phase];p=rd(out/'process.json');inv=rd(A/(phase+'-invocation.json'));host=rd(A/(phase+'-posthost.json'))
    checks[phase+'_audit_accepted']=audit['all_passed'] and all(audit['checks'].values())
    checks[phase+'_audit_hashes']=all(sha(n)==h for n,h in audit['sha256'].items())
    checks[phase+'_all_launch_pins']=check_pins(rd(A/(phase+'-launch-pins.json')))
    checks[phase+'_all_sealed_pins']=check_pins(rd(A/(phase+'-sealed-pins.json')))
    checks[phase+'_process_closed']=not host['matches'] and all(p[k][v] in host['groups'] for k in ('runner','child') for v in ('pgid','sid'))
    checks[phase+'_exit']=p['returncode']==cfg['expected_exit'] and p['reason']=='exit'+str(cfg['expected_exit'])
    checks[phase+'_bounded']=inv['elapsed_seconds']<=cfg['seconds'] and not inv['supervisor']['soft_timeout'] and not inv['supervisor']['hard_timeout']
    raw=tomllib.loads((out/'raw.toml').read_text()) if (out/'raw.toml').exists() else None
    checks[phase+'_counts']=raw is not None and raw['completed'] and raw['fatal']=='' and len(raw['groups'])==len(cfg['groups']) and all(row['name']==g['name'] and [row[n] for n in ('pass','fail','error','broken')]==g['counts'] for row,g in zip(raw['groups'],cfg['groups']))
    samples=[json.loads(line) for line in (out/'resources.jsonl').read_text().splitlines()]+[p['terminal_memory']]
    checks[phase+'_resources']=all(v['available_kib']>=6*1024**2 and v['swap_used_kib']<=1024**2 for v in samples)
    results[phase]=dict(elapsed_including_launch=inv['elapsed_seconds'],exit=p['returncode'],groups=len(host['groups']),audit_checks=len(audit['checks']),raw=raw,memory_samples=len(samples)-1,min_available_kib=min(v['available_kib'] for v in samples),max_swap_kib=max(v['swap_used_kib'] for v in samples),launch_pins=len(rd(A/(phase+'-launch-pins.json'))['inventory']),warning_present='WARNING:' in (out/'run.log').read_text())
    paths=[q for q in out.rglob('*') if q.is_file()]+[q for q in A.glob(phase+'-*') if q.is_file()]+[A/('stage-'+phase+'-review.md')]
    bindings.update({str(q.relative_to(R)):sha(q) for q in paths})
baseline=rd(D.parent/'DIRECT-LU-PREPARATION/baseline.json')
checks['source_test_CI_514_unchanged']=all(sha(R/n)==h for n,h in baseline['sha256'].items())
checks['master_unchanged']=subprocess.check_output(['git','rev-parse','master'],cwd=R,text=True).strip()=='6f68e24e8ddac42b948da8fcc2d636c010751194'
result=dict(all_passed=all(checks.values()),checks=checks,results=results,sha256=bindings,scope='New post-execution source/hash/raw reconciliation; no Julia/old auditor replay; this script is not a launch pin')
with (D/'postcheck.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=checks,results=results),indent=2))
if not result['all_passed']:raise SystemExit(1)
