"""Exclusive offline audit for S4-I. Never rerun against accepted evidence."""
from pathlib import Path
import json,tomllib,hashlib,struct,subprocess
from fractions import Fraction as Q
r=Path.cwd();d=r/'diagnostics/simplex-core-architecture';o=d/'results/S4-I';b=r/'.superpowers/simplex-core-architecture/S4-I/assembly-1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
a=tomllib.loads((b/'report.toml').read_text());p=json.loads((b/'process.json').read_text());pins=json.loads((b.parent/'assembly-1-pins.json').read_text());pre=json.loads((o/'preflight.json').read_text());host=json.loads((o/'host-after.json').read_text());cl=json.loads((o/'clone-source.json').read_text());inp=json.loads((o/'exact-inputs.json').read_text())
def q(s):return Q.from_float(struct.unpack('>d',bytes.fromhex(s))[0])
def vec(s):return list(map(q,s))
def mat(s):
 A=[[Q(0) for j in range(s['n'])] for i in range(s['m'])]
 for j in range(s['n']):
  for k in range(s['colptr'][j]-1,s['colptr'][j+1]-1):A[s['rowval'][k]-1][j]=q(s['bits'][k])
 return A
def norm(x):return max(map(abs,x),default=Q(0))
def checkeq(M,z,rhs):
 res=[sum(x*y for x,y in zip(row,z))-v for row,v in zip(M,rhs)];limit=Q(1,2**46)*max(1,max(sum(map(abs,row)) for row in M)*norm(z),norm(rhs))
 return {'residual':list(map(str,res)),'bound':str(limit),'pass':norm(res)<=limit}
exact=[];recipes=True
B1=[[4,1],[1,3]];minus=[[-1,0],[0,-1]]
for i,s in enumerate(a['solves']):
 M=mat(s['matrix']);exp=B1 if i%6 in (0,1,4,5) else minus;t=i%6 in (1,3,5);recipes &= M==exp and s['transpose']==t and vec(s['rhs'])==[1,2]
 if t:M=list(map(list,zip(*M)))
 exact.append({'label':s['label'],**checkeq(M,vec(s['solution']),vec(s['rhs']))})
reconstruction=[];bounds=True;state_recipes=True
for side in a['records']:
 A=mat(side['model']['A']);bounds &= A==inp['A'] and vec(side['model']['objective'])==list(range(1,6)) and vec(side['model']['column_lower'])==[0]*5 and vec(side['model']['row_lower'])==vec(side['model']['row_upper'])==[1,2]
 M=[row+[-int(i==j) for j in range(2)] for i,row in enumerate(A)]
 for key,expected_basis in [('initial',[6,7]),('B1',[1,2]),('B2',[3,2]),('slack',[6,7])]:
  s=side[key];idx=[j-1 for j in s['basis']];x=vec(s['point']);rho=vec(s['rho']);cost=vec(s['costs']);B=[[row[j] for j in idx] for row in M];rhs=[-sum(row[j]*x[j] for j in range(7) if j not in idx) for row in M]
  state_recipes &= s['basis']==expected_basis and mat(s['assembly'])==B and cost==inp['costs'] and all(x[j]==(0 if j<5 else j-4) for j in range(7) if j not in idx)
  primal=checkeq(B,[x[j] for j in idx],rhs);dual=checkeq(list(map(list,zip(*B))),rho,[cost[j] for j in idx]);prices=vec(s['prices']);expect=[0 if j in idx else cost[j]-sum(M[i][j]*rho[i] for i in range(2)) for j in range(7)];diff=[u-v for u,v in zip(prices,expect)];limit=Q(1,2**46)*max(1,norm(cost),max(sum(abs(M[i][j]*rho[i]) for i in range(2)) for j in range(7)))
  reconstruction.append({'side':side['side'],'state':key,'rhs':list(map(str,rhs)),'primal':primal,'dual':dual,'prices_residual':list(map(str,diff)),'prices_bound':str(limit),'prices_pass':norm(diff)<=limit})
source=(r/'src/huangfu_hall_factorization.jl').read_text();hh=source[source.index('_hh_refactor_lu!(F::Float64UMFPACK'):source.index('function copy_basis_factorization(f::HuangfuHall')];ss=(r/'src/simplex.jl').read_text();re=ss[ss.index('function recompute!(workspace::SimplexWorkspace{T};'):ss.index('recompute!(workspace::SimplexWorkspace, refactorize::Bool)')]
back=cl['hh_clone'].replace('_s4i_refactor_lu!','_hh_refactor_lu!').replace('_s4i_refactor_backend','_hh_refactor_backend').replace('function _s4i_refactorize!','function refactorize!').replace('reuse_symbolic=_same_umfpack_pattern(F,convert(SparseMatrixCSC{Float64,Int},B))','reuse_symbolic=false')
rb=cl['recompute_clone'].replace('function _s4i_recompute!','function recompute!').replace('_s4i_refactorize!(workspace.factorization, B)','refactorize!(workspace.factorization, B)')
resource=[json.loads(x) for x in (b/'resources.jsonl').read_text().splitlines()];rows=a['records'];old=tomllib.loads((d/'results/S4-G/publication-1-report.toml').read_text())['records'][0]['control_bits']
checks={
'exit0':p['returncode']==0 and p['reason']=='exit0',
'guard_pins':p['pins_unchanged'] and sha(b.parent/'assembly-1-pins.json')==p['pins_sha256'],
'all_pins_rehashed':all(Path(k).resolve()==Path(v['resolved']) and sha(k)==v['sha256'] for k,v in pins['inventory'].items()),
'55_runtime_checks':a['complete'] and 'error' not in a and len(a['checks'])==55 and all(a['checks'].values()),
'entry_budget':a['entries']==pre['calls'],
'two_sides':len(rows)==2 and [x['side'] for x in rows]==['reference','candidate'] and all(x['complete'] for x in rows),
'twelve_direct_recipes':len(exact)==12 and recipes,
'direct_exact_bounds':all(x['pass'] for x in exact),
'actual_model_bits':bounds and all(struct.pack('>d',float(k)).hex()==v for k,v in inp['bits'].items()),
'eight_reconstruction_recipes':len(reconstruction)==8 and state_recipes,
'sixteen_reconstruction_solves':all(x['primal']['pass'] and x['dual']['pass'] for x in reconstruction),
'eight_price_bounds':all(x['prices_pass'] for x in reconstruction),
'exact_source_clones':hh==back==cl['hh_original'] and re==rb==cl['recompute_original'] and (d/'reproduce/hh_borrowed_assembly_clone.jl').read_text()==cl['hh_clone']+cl['recompute_clone'],
'frozen_source_identity':all((b.parent/'assembly-1-source'/n).read_bytes()==(d/'reproduce'/n).read_bytes() for n in ['hh_borrowed_assembly.jl','hh_borrowed_assembly_clone.jl']) and a['clone_sha']==sha(d/'reproduce/hh_borrowed_assembly_clone.jl') and pre['driver_sha256']==sha(d/'reproduce/hh_borrowed_assembly.jl'),
'controls_default':all(x['controls']==old for x in rows),
'symbolic_decisions':all(x['same_pattern_symbolic_same']==(x['side']=='candidate') for x in rows),
'singular_factor_state':all(x['exception']=='SingularException' and x['native_status']==1 and x['factor_before_failure']==x['factor_after_failure'] and x['saved_before_failure']==x['saved_after_failure'] for x in rows),
'workspace_partial_mutation':all(x['after_failure']['basis']==[4,5] and mat(x['after_failure']['assembly'])==[[1,2],[2,4]] and x['after_failure']['mask']==[False,False,False,True,True,False,False] for x in rows),
'no_failure_reconstruction':all(all(x['before_failure'][k]==x['after_failure'][k] for k in ['point','rho','prices','events','counts','refactors','iterations']) for x in rows),
'kernel_totals':all(all(v==(4 if k in ['ftran','btran','refactorization'] else 0) for k,v in x['after_failure']['kernels'].items()) for x in rows),
'exact_events':all(x['after_failure']['events']==['refactor_initial']+['refactor_other']*3 and x['after_failure']['refactors']==3 and x['after_failure']['iterations']==0 for x in rows),
'no_cache_fabrication':all(x['after_failure']['pool_absent'] and x['after_failure']['hyper_absent'] for x in rows),
'actual_source':a['source']==str(r/'src'),
'native_library_pin':a['native_sha']==sha(a['native_path'])==pre['native_libraries'][a['native_path']],
'globals':a['threads']==a['blas_threads']==1 and a['precision']==256 and a['rounding']=='RoundingMode{:Nearest}()',
'host_groups_absent':not host['matches'] and host['boot_id']==p['runner']['boot_id']==p['child']['boot_id'],
'user6':len(pre['user_hashes'])==6 and all(sha(k)==v for k,v in pre['user_hashes'].items()),
'production_test_CI_unchanged':not subprocess.check_output(['git','diff','master','--','src','test','.github'],text=True),
'resources':bool(resource) and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resource)}
result={'checks':checks,'all_passed':all(checks.values()),'pins':len(pins['inventory']),'direct_exact':exact,'reconstruction':reconstruction,'raw_sha':sha(b/'report.toml'),'resources':{'samples':len(resource),'min_available_kib':min(x['available_kib'] for x in resource),'max_swap_kib':max(x['swap_used_kib'] for x in resource)}}
with (o/'assembly-1-audit.json').open('x') as f:json.dump(result,f,indent=2)
for n in ['report.toml','process.json','resources.jsonl','run.log']:
 with (o/('assembly-1-'+n)).open('xb') as f:f.write((b/n).read_bytes())
for src,name in [(b.parent/'assembly-1-pins.json','assembly-1-pins.json'),(Path('/tmp/s4-i-prepare.py'),'prepare.py.txt'),(Path('/tmp/s4-i-preflight.py'),'preflight.py.txt'),(Path('/tmp/jsimplex-hh-assembly-attempt.py'),'launcher.py.txt'),(d/'reproduce/hh_borrowed_assembly.jl','driver.jl.txt'),(d/'reproduce/hh_borrowed_assembly_clone.jl','clone.jl.txt')]:
 with (o/name).open('xb') as f:f.write(src.read_bytes())
print(json.dumps({k:v for k,v in result.items() if k not in ['direct_exact','reconstruction']},indent=2));raise SystemExit(0 if result['all_passed'] else 1)
