"""New post-return summary; reads saved audit and records, never reruns it."""
from pathlib import Path
import json,sys,tomllib
Q=Path(__file__).resolve().parent;P=Q.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-GC-DRIVER');sys.path.insert(0,str(P));import control as c
run=P/'runs/redgc300';out=run/'output';outer=P/'outers/redgc300';checks={}
def ck(n,v):checks[n]=bool(v)
a=c.rd(run/'audit.json');p=c.rd(out/'process.json');inv=c.rd(run/'invocation.json');closure=c.rd(run/'outer-closure.json');outcome=c.rd(outer/'outer-outcome.json');raw=tomllib.loads((out/'raw.toml').read_text()) if (out/'raw.toml').exists() else None
s=c.rd(run/'sealed.json');pins=c.rd(run/'launch-pins.json')
ck('seal_launch_current_hashes',c.guard.pins_match(s) and c.guard.pins_match(pins))
ck('outer_closure',closure['all_passed'] is True and c.host_safe(closure['host']) and c.bindings(closure))
ck('outer_identity',outcome['identity']==closure['outer_identity']==s['outer_identity'])
ck('audit_saved_bindings',c.bindings(a))
ck('original_failed_RED_unchanged',c.rd(P.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER')/'runs/red300/audit.json')['all_passed'] is False)
ck('prior_publication_preserved',c.bindings(c.rd(P/'publication.json')))
ck('refs_unchanged',c.git('rev-parse','HEAD')=='18ab2a17b16508833d16b83cdcfb832a7c422c18' and c.git('rev-parse','master')==c.MASTER)
ck('numerical_expected_RED',a.get('all_passed') is True and a.get('pure_timeout') is False and p['returncode']==1 and p['reason']=='exit1' and outcome['returncode']==0)
windows=sorted(out.glob('window-*.toml'));preps=sorted(out.glob('preparation-*.toml'));rows=[tomllib.loads(f.read_text()) for f in windows];preprows=[tomllib.loads(f.read_text()) for f in preps]
ck('exact_windows_and_preparations',len(windows)==60 and len(preps)==3)
ck('raw_complete_counts',raw is not None and raw.get('complete') is True and raw.get('fatal')=='' and raw.get('preparation_calls')==raw.get('preparations_completed')==3)
ck('three_exact_failures',raw is not None and len(raw['tests']['children'])==3 and all(z['fail']==1 and z['pass']==z['error']==z['broken']==0 for z in raw['tests']['children']))
ck('observed_compile_zero',all(r['compile_seconds']==r['recompile_seconds']==0 for r in rows if r['measured']))
checks_record=dict(all_passed=all(checks.values()),checks=checks,phase='redgc300',process_returncode=p['returncode'],audit_all_passed=a['all_passed'],pure_timeout=a['pure_timeout'],windows=len(windows),saved_outputs=sum(len(r['outputs']) for r in rows),preparations=preprows,allocation=a.get('allocation'),guard_elapsed_seconds=p['elapsed_including_launch'],supervisor_elapsed_seconds=inv['supervisor']['elapsed_seconds'],outer_elapsed_with_checks_seconds=outcome['elapsed_with_checks_seconds'],scope='Read-only result summary; preparation/GC/compile timings overlap, no subtractive speedup/native-free claim',sha256={str(f):c.sha(f) for f in [run/'audit.json',out/'process.json',run/'invocation.json',run/'outer-closure.json',outer/'outer-outcome.json',Q/'postcheck.py']+windows+preps+([out/'raw.toml'] if raw is not None else [])})
c.save(Q/'postcheck.json',checks_record)
print(json.dumps(dict(all_passed=checks_record['all_passed'],checks=len(checks),failed=[k for k,v in checks.items() if not v],windows=len(windows),outputs=checks_record['saved_outputs'],preparations=len(preps),audit_all_passed=a['all_passed'],pure_timeout=a['pure_timeout'],error=a.get('error'),supervisor_seconds=inv['supervisor']['elapsed_seconds'])))
