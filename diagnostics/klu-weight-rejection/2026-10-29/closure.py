from pathlib import Path
import json,hashlib,tomllib,subprocess,re
D=Path(__file__).resolve().parent;W=D.parents[2];M=Path('/home/jspitz/JSimplex.jl');checks={};bindings={}
def read(p):
 p=Path(p);data=p.read_bytes();bindings[str(p)]=hashlib.sha256(data).hexdigest();return data
def require(name,v):
 checks[name]=bool(v)
 if not v:raise RuntimeError(name)
def verify(mapping,prefix):
 for p,expected in mapping.items():
  expected=expected if isinstance(expected,str) else expected['sha256']
  require(prefix+':'+p,hashlib.sha256(read(p)).hexdigest()==expected)
r=tomllib.loads(read(D/'results-1.toml').decode());a=json.loads(read(D/'audit.json'))
for name in ['admission','results']:
 rev=json.loads(read(D/f'review-{name}.json'))
 require(name+'_review',rev.get('accepted') is True and bool(rev.get('checks')) and all(rev['checks'].values()))
 verify(rev['bindings'],name+'_binding')
require('offline_audit',a.get('accepted') is True and all(a['checks'].values()))
verify(a['bindings'],'audit_binding')
launch=json.loads(read(D/'launch-pins.json'));verify(launch['inventory'],'launch_binding')
old=json.loads(read(D/'source-pins.json'))
for p,item in old['inventory'].items():
 actual=D/'driver.before-review.jl' if p==str(D/'driver.jl') else Path(p)
 require('historical_pin:'+p,hashlib.sha256(read(actual)).hexdigest()==item['sha256'])
p=json.loads(read(D/'diagnosis-1/guard/process.json'));h=json.loads(read(D/'diagnosis-1/postflight.json'));s=json.loads(read(D/'diagnosis-1/supervisor.json'))
require('guard_pass',p['reason']=='exit0' and p['returncode']==0 and p['pins_unchanged'] and s['accepted'])
require('groups_sessions_closed',not h['conflicts'] and len(h['checked_groups'])==725 and all(p[k][f] in h['checked_groups'] for k in ['runner','child'] for f in ['pgid','sid']))
log=read(D/'diagnosis-1/guard/run.log').decode()
require('ordinary_test_pass',bool(re.search(r'First rejected KLU weight RHS\s*\|\s*76\s+76\s',log)) and 'Test Failed' not in log and 'Error During Test' not in log)
require('complete_three_arms',r['completed'] and [x['name'] for x in r['arms']]==['native-KLU','local-KLU','UMFPACK'])
require('genuine_solve_budget',sum(x['correction_calls'] for x in r['arms'])==3 and all(x['correction_calls']==1 for x in r['arms']))
require('unmodified_tolerance',all(x['policy']['solve_tolerance']==2**-44 and not x['policy']['solve_refinement'] and x['policy']['max_refinements']==3 for x in r['arms']))
require('quality_not_improved',all(x['corrections'][0]['gate']=='quality_not_improved' and not x['corrections'][0]['accepted'] and x['initial']['point_hash']==x['final']['point_hash'] for x in r['arms']))
for arm in r['arms']:
 snapshots=[arm['initial'],arm['final'],arm['corrections'][0]['before'],arm['corrections'][0]['trial']]
 for snap in snapshots:
  q=snap['quality'];require('exact_refusal:'+arm['name']+':'+snap['label'],not q['reliable'] and q['relative_error']==1.0 and any(e['arm']==arm['name'] and e['snapshot']==snap['label'] and e['ratio']=='1' and e['exceeds_tolerance'] for e in a['selected_exact_equations']))
require('umfpack_no_internal_refinement',r['arms'][2]['controls']['IRSTEP']==0)
w=r['witness'];require('witness_retained',Path(w['path']).stat().st_size==w['bytes'] and hashlib.sha256(read(w['path'])).hexdigest()==w['sha256'])
for pth in (M/'src').rglob('*.jl'):
 require('production_identity:'+str(pth.relative_to(M)),read(pth)==read(W/pth.relative_to(M)))
for ref in ['HEAD','master','origin/master']:
 value=subprocess.check_output(['git','-C',str(M),'rev-parse',ref],text=True).strip();require('master_'+ref,value=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b')
require('diagnostic_original_head',subprocess.check_output(['git','-C',str(W),'rev-parse','HEAD'],text=True).strip()=='c0c4d7712dba3955041671cd2d5eaaba6a83dbf2')
require('tracked_worktree_untouched',subprocess.run(['git','-C',str(W),'diff','--quiet','HEAD','--']).returncode==0)
read(D/'REPORT.md');read(D/'REVIEW-RESULTS.md');read(D/'closure.py')
result=dict(accepted=True,scope='diagnostic closure only; prior weight experiment remains rejected',checks=checks,bindings=bindings)
(D/'closure.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'accepted':True,'checks':len(checks),'bindings':len(bindings)}))
