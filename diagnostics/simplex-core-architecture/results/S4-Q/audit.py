from pathlib import Path
from fractions import Fraction as F
import hashlib,json,tomllib,struct,statistics,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-Q';raw=R/'.superpowers/simplex-core-architecture/S4-Q/cost-1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();q=lambda h:F.from_float(struct.unpack('>d',bytes.fromhex(h))[0]);a=tomllib.loads((E/'cost-1-report.toml').read_text());p=json.loads((E/'cost-1-process.json').read_text());pins=json.loads((E/'cost-1-pins.json').read_text());pre=json.loads((E/'preflight.json').read_text());x=json.loads((D/'results/S4-P/exact-inputs.json').read_text());checks={}
def ck(k,v):checks[k]=bool(v)
ck('exit0',p['returncode']==0 and p['reason']=='exit0');ck('complete6176',a['complete'] and sum(l['checks'] for l in a['lifecycles'])==6176);ck('full558pins',len(pins['inventory'])==558 and all(sha(f)==v['sha256'] for f,v in pins['inventory'].items()));ck('process_pin_hash',sha(raw/'pins.json')==p['pins_sha256'] and p['pins_unchanged']);ck('raw_portable4',all(sha(raw/n)==sha(E/('cost-1-'+n)) for n in ['report.toml','process.json','run.log','resources.jsonl']));ck('source_actual',a['source']==str(R/'src'));ck('user6',all(sha(f)==h for f,h in pre['user_hashes'].items()));ck('master_source_test_ci',not subprocess.check_output(['git','diff','master','--','src','test','.github']));ck('driver_clone_input_runtime_sha',a['clone_sha256']==pre['clone_sha256']==sha(D/'reproduce/hh_history_cost_clone.jl') and a['inputs_sha256']==pre['input_toml_sha256']==sha(E/'inputs.toml') and sha(D/'reproduce/hh_history_cost.jl')==pre['driver_sha256']);ck('native_actual_pinned',sha(a['native_path'])==a['native_sha256']==pre['native_libraries'][a['native_path']]);ck('single_threads',a['threads']==a['blas_threads']==1)
c=(D/'reproduce/hh_history_cost_clone.jl').read_text();back=c.replace('_s4q_refactor_lu!','_hh_refactor_lu!').replace('_s4q_refactor_backend','_hh_refactor_backend').replace('function _s4q_refactorize!','function refactorize!').replace('reuse_symbolic=_same_umfpack_pattern(F,convert(SparseMatrixCSC{Float64,Int},B))','reuse_symbolic=false');s=(R/'src/huangfu_hall_factorization.jl').read_text();part=s[s.index('_hh_refactor_lu!(F::Float64UMFPACK'):s.index('function copy_basis_factorization(f::HuangfuHall')];ck('inverse_clone',back==part==(E/'production-refactor.txt').read_text())
ls=a['lifecycles'];expected=[(w,r,f,c) for w,num in [(True,2),(False,8)] for r in range(1,num+1) for f in ['sparse','dense'] for c in ([False,True] if r%2 else [True,False])];ck('exact_schedule40',[(l['warmup'],l['round'],l['fixture'],l['candidate']) for l in ls]==expected)
ck('counts_eachlife',all(l['counts']==[1,2,6,6,9,9] and l['completed_solves']==24 and l['done'] for l in ls));ck('whole_entries',a['entries']==dict(constructor=40,refactor=80,update=240,preparedF=240,ordinaryF=360,B=360,gc_pre=40,gc_post=40));ck('all_timing120_valid',all(t['valid'] for l in ls for t in l['timings']));ck('measured96_compile0',sum(not l['warmup'] for l in ls)==32 and all(t['compile_seconds']==t['recompile_seconds']==0 for l in ls if not l['warmup'] for t in l['timings']));ck('default_controls_same',all(l['control_bits']==ls[0]['control_bits'] for l in ls));ck('gc_eachlife',all(l['gc_pre']==l['gc_post']==1 for l in ls));ck('output_shape',all(len(l['output_bits'])==24 and all(len(v)==48 for v in l['output_bits']) for l in ls));ck('runtime_residuals_pass',all(0<=r<=b for l in ls for r,b in zip(l['runtime_residuals'],l['runtime_bounds'])))
inputs=tomllib.loads((E/'inputs.toml').read_text());ck('PinputSHA',sha(D/'results/S4-P/exact-inputs.json')==pre['exact_P_input_sha256']=='85874a35de281a9de4ce4d49c7f17f176d37a1597fc557ae64469202fcfd9b06');mats={};rhs={};incoming={}
for f in x['fixtures']:
 k=f['name'];mats[k]=[];rhs[k]=[];incoming[k]=[list(map(q,t['incoming_bits'])) for t in f['transitions']]
 for st in f['states']:
  assert all(inputs[k+str(st['stage'])][field]==st[field] for field in ['nnz','colptr','rowval','nzval_bits','rhsF_bits','rhsB_bits'])
  M=[[F(0) for j in range(48)] for i in range(48)]
  for j in range(48):
   for t in range(st['colptr'][j]-1,st['colptr'][j+1]-1):M[st['rowval'][t]-1][j]=q(st['nzval_bits'][t])
  mats[k].append(M);rhs[k].append((list(map(q,st['rhsF_bits'])),list(map(q,st['rhsB_bits']))))
 for t in f['transitions']:assert inputs[k+'incoming'+str(t['step'])]['bits']==t['incoming_bits']
ck('all_input_tables_bitmatch',True)
# Each tuple identifies one of the exact 24 retained solve equations, in call order.
eqs=[(0,'F'),(0,'B')]
for k in range(1,7):
 eqs +=[(k,'D'),(k,'F'),(k,'B')]
 if k in (3,6):eqs +=[(k,'F'),(k,'B')]
records=[]
for il,l in enumerate(ls):
 fixture=l['fixture']
 for io,((stage,mode),out) in enumerate(zip(eqs,l['output_bits'])):
  M=mats[fixture][stage-1 if mode=='D' else stage]
  if mode=='B':M=list(map(list,zip(*M)))
  b=incoming[fixture][stage-1] if mode=='D' else rhs[fixture][stage][mode=='B'];z=list(map(q,out))
  r=max(abs(sum(v*zz for v,zz in zip(row,z))-bb) for row,bb in zip(M,b));scale=max(F(1),max(sum(map(abs,row)) for row in M)*max(map(abs,z)),max(map(abs,b)));bound=F(64,2**52)*scale
  records.append(dict(lifecycle=il+1,output=io+1,stage=stage,mode=mode,residual=str(r),bound=str(bound),ratio=float(r/bound),passed=r<=bound))
ck('exact960residuals',len(records)==960 and all(t['passed'] for t in records));ck('all960residuals_nonzero',all(F(t['residual'])!=0 for t in records))
pairs=[]
for f in ['sparse','dense']:
 for rnd in range(1,9):
  side=[next(l for l in ls if not l['warmup'] and l['fixture']==f and l['round']==rnd and l['candidate']==c) for c in [False,True]]
  pairs.append(dict(fixture=f,round=rnd,outputs_equal=side[0]['output_bits']==side[1]['output_bits'],outer_ratio=side[1]['timings'][0]['seconds']/side[0]['timings'][0]['seconds'],inner_ratios=[side[1]['timings'][i]['seconds']/side[0]['timings'][i]['seconds'] for i in [1,2]]))
ck('16pairs_captured',len(pairs)==16)
def summary(v):
 med=statistics.median(v);return dict(median=med,min=min(v),max=max(v),mad=statistics.median([abs(x-med) for x in v]))
stats={}
for f in ['sparse','dense']:
 ps=[p for p in pairs if p['fixture']==f];obj={'outer_paired_ratio':summary([p['outer_ratio'] for p in ps]),'inner1_paired_ratio':summary([p['inner_ratios'][0] for p in ps]),'inner2_paired_ratio':summary([p['inner_ratios'][1] for p in ps]),'equal_output_pairs':sum(p['outputs_equal'] for p in ps)}
 for c in [False,True]:
  v=[l for l in ls if not l['warmup'] and l['fixture']==f and l['candidate']==c];obj['candidate' if c else 'reference']={name:{field:summary([l['timings'][i][field] for l in v]) for field in ['seconds','bytes','allocations','gc_seconds']} for i,name in enumerate(['outer','inner1','inner2'])}
 stats[f]=obj
resources=[json.loads(l) for l in (E/'cost-1-resources.jsonl').read_text().splitlines()];ck('resource_guards',all(r['available_kib']>=6*1024**2 and r['swap_used_kib']<=1024**2 for r in resources));host=json.loads((E/'host-after.json').read_text());ck('whole_groups_absent',not host['matches'] and not host['pids_present'])
res=dict(checks=checks,all_passed=all(checks.values()),pin_count=558,exact_residuals=records,pairs=pairs,statistics=stats,resource_samples=len(resources),min_available_kib=min(r['available_kib'] for r in resources),max_swap_kib=max(r['swap_used_kib'] for r in resources),raw_sha256=sha(E/'cost-1-report.toml'),auditor_sha256=sha(Path(__file__)),auditor_scope='Created post-exit, NOT a launch pin. Exact rational equations from prelaunch frozen input/output bits, no numerical rerun.',source_derived_work=dict(numeric_entries=120,extractions=120,reference_symbolic=60,candidate_initial_symbolic=20,candidate_pattern_checks=40,internal_unit_transposes=240,history_apply_entries=1200,orientation_upper_bound=120))
with (E/'audit.json').open('x') as out:json.dump(res,out,indent=2);out.write('\n')
print('checks',len(checks),'pass',sum(checks.values()),'residuals',len(records),'nonzero',sum(F(t['residual'])!=0 for t in records),'maxratio',max(t['ratio'] for t in records));print(json.dumps({f:{k:v for k,v in st.items() if k not in ['reference','candidate']} for f,st in stats.items()},indent=2));assert res['all_passed']
