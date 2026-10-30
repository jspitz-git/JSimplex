from pathlib import Path
import json,hashlib,subprocess
D=Path(__file__).resolve().parent;W=D.parents[2];M=Path('/home/jspitz/JSimplex.jl');checks={};bindings={}
S=W/'docs/superpowers/specs/2026-10-30-dual-recovery-devex-fallback-design.md';P=W/'docs/superpowers/plans/2026-10-30-dual-recovery-devex-fallback.md'
def read(p):
 p=Path(p);b=p.read_bytes();bindings[str(p)]=hashlib.sha256(b).hexdigest();return b
def require(k,v):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
def verify(mapping,prefix,stage=None):
 for path,e in mapping.items():
  actual=Path(path)
  if stage and path==str(S):actual=D/f'design.{stage}.md'
  if stage and path==str(P):actual=D/f'plan.{stage}.md'
  sha=e if isinstance(e,str) else e['sha256'];require(prefix+':'+path,hashlib.sha256(read(actual)).hexdigest()==sha)
pins=json.loads(read(D/'source-pins.json'));require('source_baseline_comparisons',pins['production_files_equal_master']==71);verify(pins['bindings'],'source')
for n,stage in [('plan-check-final.json','before-review'),('review-fix.json','after-norm-fix'),('metadata-fix.json',None)]:
 r=json.loads(read(D/n));require(n+'_pass',r['accepted'] and all(r['checks'].values()));verify(r['bindings'],n,stage)
for n,stage in [('review-initial.json','before-review'),('review-intermediate.json','after-norm-fix')]:
 r=json.loads(read(D/n));require(n+'_preserved',r['accepted'] is False);verify(r['bindings'],n,stage)
r=json.loads(read(D/'review-final.json'));require('independent_final_accepted',r['accepted'] and len(r['checks'])==20 and all(r['checks'].values()));verify(r['bindings'],'final')
f=json.loads(read(D/'initial-check-failure.json'));require('checker_failure_preserved',f['returncode']==1 and hashlib.sha256(read(D/'check-plan.py')).hexdigest()==f['source_sha256'])
h=json.loads(read(D/'host.json'));require('host_no_Julia',not h['conflicts'] and len(h['checked_groups'])==727)
require('no_candidate_or_test',not list(D.rglob('*.jl')) and '[x]' not in read(P).decode())
for p in (M/'src').rglob('*.jl'):require('production_unchanged:'+str(p.relative_to(M)),read(p)==read(W/p.relative_to(M)))
for ref in ['HEAD','master','origin/master']:require('master_'+ref,subprocess.check_output(['git','-C',str(M),'rev-parse',ref],text=True).strip()=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b')
require('diagnostic_start',subprocess.check_output(['git','-C',str(W),'rev-parse','HEAD'],text=True).strip()=='028b3efc8a60c880ddb863fb08537d0c8cc1ece1')
require('tracked_untouched',subprocess.run(['git','-C',str(W),'diff','--quiet','HEAD','--']).returncode==0)
read(D/'README.md');read(D/'REVIEW-FINAL.md');read(D/'closure.py')
(D/'closure.json').write_text(json.dumps(dict(accepted=True,implementation_admission=False,numerical_admission=False,scope='reviewed design/plan only',checks=checks,bindings=bindings),indent=2)+'\n');print(json.dumps({'accepted':True,'checks':len(checks),'bindings':len(bindings)}))
