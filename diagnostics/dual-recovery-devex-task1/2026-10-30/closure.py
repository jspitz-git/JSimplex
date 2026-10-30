from pathlib import Path
import json,hashlib,subprocess
D=Path(__file__).resolve().parent;W=D.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git','-C',str(W),*a],text=True).strip()
def require(v,m):
 if not v:raise RuntimeError(m)
checks={};bindings={}
def check(k,v):checks[k]=bool(v)
def validate(n,mapping=None):
 r=json.loads((D/n).read_text());ok=True
 for name,h in r['bindings'].items():
  p=Path((mapping or {}).get(name,name));ok=ok and sha(p)==h
 check(n+'_bindings',ok)
 return r
original=validate('source-check.json');check('original_87_source_checks',original['accepted'] and len(original['checks'])==87 and all(original['checks'].values()))
validate('source-pins.json')
validate('review-fix.json')
initial=validate('review-initial.json',{str(D/'REPORT.md'):str(D/'REPORT.md.before-review')});check('initial_rejection_preserved',not initial['accepted'] and initial['initial_findings'][0]['id']=='F1')
final=validate('review-final.json');check('final_source_review_accepted',final['accepted'] and all(final['checks'].values()))
check('final_review_report_bound',sha(D/'REVIEW-FINAL.md')==final['review_report_sha256'])
check('scope_source_only','UNEXECUTED' in (D/'REPORT.md').read_text() and 'Task4' in (D/'REPORT.md').read_text())
check('diagnostic_baseline',git('rev-parse','HEAD')=='24a79f0babfba545387bad65939b5d1b51767f56')
check('master_unchanged',git('rev-parse','master')=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b')
check('no_actual_source_test_changes',not git('diff','HEAD','--','src','test','Project.toml','.github'))
check('no_tracked_modifications',not git('diff','--name-only','HEAD'))
for p in sorted(D.iterdir()):
 if p.is_file() and p.name!='closure.json':bindings[str(p)]=sha(p)
r=dict(accepted=all(checks.values()),scope='Task1 isolated source/test preparation accepted only; runtime UNEXECUTED',numerical_admission=False,production_admission=False,checks=checks,bindings=bindings,historical_binding_maps={str(D/'review-initial.json'):{str(D/'REPORT.md'):str(D/'REPORT.md.before-review')}})
with (D/'closure.json').open('x') as f:f.write(json.dumps(r,indent=2)+'\n')
print(json.dumps(dict(accepted=r['accepted'],checks=len(checks),bindings=len(bindings))))
require(r['accepted'],'closure failed')
