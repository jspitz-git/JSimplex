"""One-shot post-exit supplement, not a launch pin or old auditor rerun."""
from pathlib import Path
import json,sys,hashlib,tomllib,subprocess
D=Path(__file__).resolve().parent;Q=D.parent/'NATIVE-PIVOT-GREEN2-PREPARATION';R=D.parents[3];RUN=Q/'runs/green2'
sys.path.insert(0,str(Q));from control import full_host,config,validate_stage,verify_review
import guard
def rd(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(p,z):
 with p.open('x') as f:json.dump(z,f,indent=2);f.write('\n')
a=rd(RUN/'audit.json');sealed=rd(RUN/'sealed.json');pins=rd(RUN/'launch-pins.json');p=rd(RUN/'output/process.json');inv=rd(RUN/'invocation.json');raw=tomllib.loads((RUN/'output/raw.toml').read_text());budget=rd(Q/'budget.json')
h=full_host(rd(RUN/'posthost.json')['groups']);save(D/'posthost.json',h)
checks=dict(audit=a['all_passed'] is True and a['error']=='',audit_bindings=all(sha(n)==v for n,v in a['sha256'].items()),seal=guard.pins_match(sealed),launch=guard.pins_match(pins),output_pins=rd(RUN/'output/pins.json')==pins,exit=p['returncode']==0 and p['reason']=='exit0' and inv['supervisor']['accepted'] is True and inv['elapsed_seconds']<=60,main_groups={g['name']:g['pass'] for g in raw['tests']['children']}==budget['test_groups'],all_tests=sum(g['pass'] for g in raw['tests']['children'])==6858 and all(g['fail']==g['error']==g['broken']==0 for g in raw['tests']['children']),regression=raw['regression_tests']['children'][0]['pass']==119 and raw['regression_tests']['children'][0]['fail']==raw['regression_tests']['children'][0]['error']==raw['regression_tests']['children'][0]['broken']==0 and raw['regression_helper_calls']==16 and raw['regression_counts_before']==raw['regression_counts_after']=={},entries_equations=len(raw['events'])==792 and len(raw['equations'])==324,process_closure=not h['matches'] and len(h['groups'])==214,refs=h['head']=='3feb815bf8a1507d5feecafaf038315b645a4243' and h['master']=='6f68e24e8ddac42b948da8fcc2d636c010751194',candidate75=len(validate_stage(config('green2')))==75,old_green_false=rd(D.parent/'NATIVE-PIVOT-QUALIFICATION/runs/green/audit.json')['all_passed'] is False,no_other_new_run={p.name for p in (Q/'runs').iterdir()}=={'green2'},actual_unchanged=subprocess.check_output(['git','diff','--name-only','--','src','test','Project.toml','.github','diagnostics/direct-lu-markowitz/reproduce'],cwd=R)==b'')
verify_review(rd(RUN/'admission.json'),RUN/'sealed.json',sealed['files']+[str(RUN/'sealed.json')],'exact-stage admission','green2');checks['admission']=True
resources=[json.loads(s) for s in (RUN/'output/resources.jsonl').read_text().splitlines()]
checks['resources']=all(z['available_kib']>=6*1024**2 and z['swap_used_kib']<=1024**2 for z in resources+[p['terminal_memory']])
for src,name in [(R/'diagnostics/simplex-core-architecture/STATUS.md','STATUS.md.before-GREEN2'),(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','roadmap.md.before-GREEN2')]:
 with (D/name).open('xb') as f:f.write(src.read_bytes())
files=[D/'postcheck.py',D/'posthost.json',RUN/'audit.json',RUN/'admission.json',RUN/'sealed.json',RUN/'launch-pins.json',RUN/'invocation.json',RUN/'output/raw.toml',RUN/'output/process.json',RUN/'output/resources.jsonl',D/'STATUS.md.before-GREEN2',D/'roadmap.md.before-GREEN2']
save(D/'postcheck.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):sha(p) for p in files},summary=dict(assertions=6977,original_assertions=6858,regression_assertions=119,selected_entries=792,equations=324,sealed_files=len(sealed['files']),launch_files=len(pins['files']),audit_bindings=len(a['sha256']),elapsed_inclusive_seconds=inv['elapsed_seconds'],resource_samples=len(resources),minimum_available_kib=min(z['available_kib'] for z in resources),maximum_swap_kib=max(z['swap_used_kib'] for z in resources),terminal_available_kib=p['terminal_memory']['available_kib'],child_maxrss_kib=p['child_maxrss_kib']),scope='Post-exit supplemental checks; not launch pins, no benchmark/native budget claim'))
if not all(checks.values()):raise RuntimeError(checks)
print(dict(checks=len(checks),bindings=len(files),all_passed=True))
