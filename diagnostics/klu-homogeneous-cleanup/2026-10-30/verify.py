from pathlib import Path
import json,tomllib,hashlib,re,struct
D=Path(__file__).resolve().parent;checks={};bindings={}
def read(p):
 p=Path(p);b=p.read_bytes();bindings[str(p)]=hashlib.sha256(b).hexdigest();return b
def require(k,v):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
def verify(mapping,prefix):
 for p,expected in mapping.items():
  sha=expected if isinstance(expected,str) else expected['sha256']
  require(prefix+':'+p,hashlib.sha256(read(p)).hexdigest()==sha)
r=tomllib.loads(read(D/'results-1.toml').decode());inputs=json.loads(read(D/'inputs.json'))
old=tomllib.loads(read(inputs['previous_results']['path']).decode());require('previous_results_hash',bindings[inputs['previous_results']['path']]==inputs['previous_results']['sha256'])
require('completed',r['completed'] is True and len(r['cases'])==6 and len(r['small_cases'])==12)
require('same_matrix',r['matrix_hash']==old['matrix_hash']==inputs['matrix_hash'] and r['n']==old['n']==28453)
require('unchanged_policy',all(r['policy']==arm['policy'] for arm in old['arms']))
require('fixed_policy',r['policy']['solve_tolerance']==2**-44 and not r['policy']['solve_refinement'] and r['policy']['max_refinements']==3)
require('six_cases',[(c['arm'],c['stage']) for c in r['cases']]==[(n,s) for n in ['native-KLU','local-KLU','UMFPACK'] for s in ['initial','post-correction']])
for c in r['cases']:
 key=c['arm']+'/'+c['stage'];o=next(a for a in old['arms'] if a['name']==c['arm']);snap=o['initial'] if c['stage']=='initial' else o['corrections'][0]['trial']
 require(key+'_saved_point',c['input_hash']==snap['point_hash'] and c['before']==snap['quality'])
 require(key+'_finite_original',c['before']['finite'] and not c['before']['reliable'] and c['before']['relative_error']==1)
 require(key+'_changes',c['changed_components']==len(c['changed_indices'])==len(c['changed_before_bits'])==len(c['changed_after_bits']) and c['changed_indices']==sorted(set(c['changed_indices'])) and all(1<=i<=r['n'] for i in c['changed_indices']))
 require(key+'_only_solution_zeros',all(h=='0000000000000000' for h in c['changed_after_bits']))
 require(key+'_adoption_rule',c['accepted']==(c['changed'] and c['proposed']['finite'] and c['proposed']['reliable']))
 require(key+'_returned_quality',c['returned']==(c['proposed'] if c['accepted'] else c['before']))
 require(key+'_returned_point_binding',c['returned_hash']==(c['proposed_hash'] if c['accepted'] else c['input_hash']))
 if c['stage']=='post-correction':require(key+'_expected_pass',c['accepted'] and c['returned']['reliable'])
 require(key+'_preparation_observations',all(k in c and isinstance(c[k],(int,float)) and c[k]>=0 for k in ['seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds']))
for T in ['Float32','Float64']:
 for transposed in [False,True]:
  rows=[c for c in r['small_cases'] if c['type']==T and c['transposed']==transposed];require(T+str(transposed)+'_three_controls',len(rows)==3)
  for c in rows:
   k=T+str(transposed)+c['case']
   if c['case']=='essential-small-components':require(k,c['before']['reliable'] and not c['proposed']['reliable'] and not c['accepted'] and c['returned']==c['before'])
   elif c['case']=='removable-small-component':require(k,not c['before']['reliable'] and c['accepted'] and c['returned']['reliable'])
   elif c['case']=='genuinely-bad-point':require(k,not c['before']['reliable'] and not c['proposed']['reliable'] and not c['accepted'] and not c['returned']['reliable'])
   else:raise RuntimeError('unknown control')
p=json.loads(read(D/'verification-1/guard/process.json'));s=json.loads(read(D/'verification-1/supervisor.json'));h=json.loads(read(D/'verification-1/postflight.json'))
require('guard_normal_exit',p['returncode']==0 and p['reason']=='exit0' and p['pins_unchanged'] and s['accepted'])
require('no_kill_timeout',not any(s.get(k,False) for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']))
require('groups_sessions_closed',not h['conflicts'] and len(h['checked_groups'])==727 and all(p[k][f] in h['checked_groups'] for k in ['runner','child'] for f in ['pgid','sid']))
for kind in ['runner','child']:require(kind+'_identity',all(k in p[kind] for k in ['boot_id','start_ticks','command','pgid','sid']))
log=read(D/'verification-1/guard/run.log').decode();m=re.search(r'Validated homogeneous cleanup\s*\|\s*(\d+)\s+(\d+)\s',log)
require('ordinary_test_pass',m is not None and m[1]==m[2] and 'Test Failed' not in log and 'Error During Test' not in log)
for name in ['source-pins.json','launch-pins.json']:verify(json.loads(read(D/name))['inventory'],name)
for k in ['tape','witness']:require(k+'_input_preserved',hashlib.sha256(read(inputs[k]['path'])).hexdigest()==inputs[k]['sha256'])
w=r['witness'];require('new_witness',Path(w['path']).stat().st_size==w['bytes'] and hashlib.sha256(read(w['path'])).hexdigest()==w['sha256'])
result=dict(accepted=True,scope='saved-point cleanup verification only, not production integration',checks=checks,bindings=bindings,test_pass_count=int(m[1]),runtime_accepted={c['arm']+'/'+c['stage']:c['accepted'] for c in r['cases']})
(D/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'accepted':True,'checks':len(checks),'bindings':len(bindings),'test_pass_count':int(m[1]),'runtime_accepted':result['runtime_accepted']}))
