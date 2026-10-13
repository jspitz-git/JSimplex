from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent;cache={}
def sh(p):
 p=Path(p);z=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):z.update(b)
 cache[str(p)]=z.hexdigest();return z.hexdigest()
def j(p):return json.loads(Path(p).read_text())
c={}
for name in ['entry.json','reconciliation-2.json','source-contract.json']:
 d=j(H/name);c[name]=d['all_passed'] is True and all(sh(p)==v for p,v in d['sha256'].items())
x=j(H/'reconciliation-2.json');c['exact82rows41groups']=len(x['rows'])==82 and all(len([y for y in x['rows'] if y['run']==run])==41 for run in ['38142752357','38149970679'])
c['only_known_historical_source_change']=len(x['comparisons'])==48 and all(y['equal'] or y['file']=='src/simplex_perturbation.jl' for y in x['comparisons'])
c['six_integrations14sources']=len(x['integrations'])==6 and all(len(y['source'])==14 and all(z['matched'] for z in y['source']) for y in x['integrations'])
c['production_tests_unchanged']=not subprocess.check_output(['git','diff','--','src','test','.github','Project.toml'])
c['master_unchanged']=subprocess.check_output(['git','rev-parse','master'],text=True).strip()=='d02416c108f06fcd41d58e0a1980b70a51fef9ef'
bind={str(p):sh(p) for p in [H/'entry.json',H/'reconciliation-2.json',H/'source-contract.json',D/'S5-HANDOFF-COVERAGE-RECONCILIATION.md',R/'docs/superpowers/plans/2026-10-13-cleanup-entry-reuse-design-decision.md',H/'independent.py']}
with (H/'independent.json').open('x') as f:json.dump(dict(checks=c,all_passed=all(c.values()),read_time_files=len(cache),sha256=bind),f,indent=2);f.write('\n')
print(json.dumps(dict(checks=c,files=len(cache),bindings=len(bind))));assert all(c.values())
