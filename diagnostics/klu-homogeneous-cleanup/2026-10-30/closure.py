from pathlib import Path
import hashlib,json,tomllib,subprocess,re
D=Path(__file__).resolve().parent;W=D.parents[2];M=Path('/home/jspitz/JSimplex.jl');checks={};bindings={}
def read(p):
 p=Path(p);b=p.read_bytes();bindings[str(p)]=hashlib.sha256(b).hexdigest();return b
def require(k,v):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
def verify(mapping,prefix):
 for p,e in mapping.items():
  sha=e if isinstance(e,str) else e['sha256'];require(prefix+':'+p,hashlib.sha256(read(p)).hexdigest()==sha)
for name in ['admission','results']:
 rev=json.loads(read(D/f'review-{name}.json'));require(name+'_review',rev.get('accepted') is True and bool(rev['checks']) and all(rev['checks'].values()));verify(rev['bindings'],name)
a=json.loads(read(D/'rejection-analysis.json'));require('rejection_classification',a['diagnostic_accepted'] is True and a['candidate_accepted'] is False and all(a['checks'].values()));verify(a['bindings'],'classification')
for name in ['source-pins.json','launch-pins.json']:verify(json.loads(read(D/name))['inventory'],name)
r=tomllib.loads(read(D/'results-1.toml').decode());require('all_six_refused',r['completed'] and len(r['cases'])==6 and all(not c['accepted'] and not c['returned']['reliable'] and c['returned_hash']==c['input_hash'] and c['returned']==c['before'] for c in r['cases']))
require('original_policy',r['policy']['solve_tolerance']==2**-44 and not r['policy']['solve_refinement'] and r['policy']['max_refinements']==3)
require('twelve_small_controls',len(r['small_cases'])==12)
for c in r['small_cases']:
 if c['case']=='essential-small-components':require(c['type']+str(c['transposed'])+'_needed_tiny_preserved',c['before']['reliable'] and not c['proposed']['reliable'] and not c['accepted'] and c['returned']==c['before'])
p=json.loads(read(D/'verification-1/guard/process.json'));h=json.loads(read(D/'verification-1/postflight.json'));s=json.loads(read(D/'verification-1/supervisor.json'))
require('failure_preserved',p['reason']=='exit1' and p['returncode']==1 and p['pins_unchanged'] and not s['accepted'])
require('no_timeout_or_kill',not any(s.get(k,False) for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']))
require('closed_groups_sessions',not h['conflicts'] and len(h['checked_groups'])==727 and all(p[k][f] in h['checked_groups'] for k in ['runner','child'] for f in ['pgid','sid']))
log=read(D/'verification-1/guard/run.log').decode();require('exact99pass3fail',bool(re.search(r'Validated homogeneous cleanup\s*\|\s*99\s+3\s+102\s',log)) and log.count('Expression: a.accepted && q.reliable')==3 and log.count('Test Failed at ')==3 and 'Error During Test' not in log)
strict=json.loads(read(D/'strict-auditor-rejection.json'));require('strict_auditor_still_failed',strict['returncode']==1 and not strict['expected_acceptance'])
w=r['witness'];require('witness_retained',Path(w['path']).stat().st_size==w['bytes'] and hashlib.sha256(read(w['path'])).hexdigest()==w['sha256'])
for p in (M/'src').rglob('*.jl'):require('production_identity:'+str(p.relative_to(M)),read(p)==read(W/p.relative_to(M)))
for ref in ['HEAD','master','origin/master']:require('master_'+ref,subprocess.check_output(['git','-C',str(M),'rev-parse',ref],text=True).strip()=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b')
require('original_diagnostic_head',subprocess.check_output(['git','-C',str(W),'rev-parse','HEAD'],text=True).strip()=='8b97ba6887f940e500a48c9a6a00f6041d62f5a4')
require('tracked_untouched',subprocess.run(['git','-C',str(W),'diff','--quiet','HEAD','--']).returncode==0)
read(D/'REPORT.md');read(D/'REVIEW-RESULTS.md');read(D/'closure.py')
(D/'closure.json').write_text(json.dumps(dict(accepted=True,candidate_accepted=False,scope='closure of FAILED verification; diagnostic classification only',checks=checks,bindings=bindings),indent=2)+'\n');print(json.dumps({'accepted':True,'candidate_accepted':False,'checks':len(checks),'bindings':len(bindings)}))
