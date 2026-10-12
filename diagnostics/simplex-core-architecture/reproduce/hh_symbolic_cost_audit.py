"""S4-M exclusive postexit audit; separately hashed, NOT a launch pin."""
from pathlib import Path
from fractions import Fraction as Q
import json,tomllib,struct,hashlib,statistics,subprocess
r=Path.cwd();d=r/'diagnostics/simplex-core-architecture';o=d/'results/S4-M';raw=r/'.superpowers/simplex-core-architecture/S4-M/cost-1'
a=tomllib.loads((raw/'report.toml').read_text());p=json.loads((raw/'process.json').read_text());pins=json.loads((raw/'pins.json').read_text());oracle=json.loads((o/'exact-inputs.json').read_text());pre=json.loads((o/'preflight.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks={};ck=lambda k,v:checks.__setitem__(k,bool(v));ck('exit0',p['returncode']==0 and p['reason']=='exit0');ck('runtime231',a['complete'] and len(a['checks'])==231 and all(a['checks'].values()));ck('pins554',len(pins['inventory'])==554 and all(sha(k)==v['sha256'] for k,v in pins['inventory'].items()));ck('raw_portable4',all(sha(raw/n)==sha(o/('cost-1-'+n)) for n in ['report.toml','run.log','process.json','resources.jsonl']));ck('source_actual',a['source']==str(r/'src'));ck('thread_precision',a['threads']==a['blas_threads']==1 and a['precision']==256);ck('input_driver_clone_hash',sha(o/'inputs.toml')==pre['input_sha256']==a['input_sha256'] and sha(d/'reproduce/hh_symbolic_cost.jl')==pre['driver_sha256'] and sha(d/'reproduce/hh_symbolic_cost_clone.jl')==pre['clone_sha256']==a['clone_sha256']);ck('native_hash',sha(a['native_path'])==a['native_sha256']==pre['native_libraries'][a['native_path']]);ck('user6',all(sha(k)==h for k,h in pre['user_hashes'].items()))
s=(r/'src/huangfu_hall_factorization.jl').read_text();production=s[s.index('_hh_refactor_lu!(F::Float64UMFPACK'):s.index('function copy_basis_factorization(f::HuangfuHall')];clone=(d/'reproduce/hh_symbolic_cost_clone.jl').read_text();back=clone.replace('_s4m_refactor_lu!','_hh_refactor_lu!').replace('_s4m_refactor_backend','_hh_refactor_backend').replace('function _s4m_refactorize!','function refactorize!').replace('reuse_symbolic=_same_umfpack_pattern(F,convert(SparseMatrixCSC{Float64,Int},B))','reuse_symbolic=false');ck('inverse_exact',back==production==(o/'production-refactor.txt').read_text())
ck('work_budget',a['entries']=={'constructor':4,'refactor':640,'FTRAN':44,'BTRAN':44});ck('samples_endpoints_memory',len(a['samples'])==40 and len(a['endpoints'])==44 and len(a['checkpoints'])==3 and len(a['setups'])==4)
meas=[v for v in a['samples'] if not v['warmup']];warm=[v for v in a['samples'] if v['warmup']];ck('compile_zero32',len(meas)==32 and all(v['compile_seconds']==v['recompile_seconds']==0 for v in meas));ck('warm8',len(warm)==8)
expected=[]
for rnd in range(1,9):
 for kind in ['sparse','dense']:
  for side in (['reference','candidate'] if rnd%2 else ['candidate','reference']):expected.append((rnd,kind,side,((rnd-1)//2)%2))
ck('balanced_order_exact',[(v['round'],v['kind'],v['side'],v['phase']) for v in meas]==expected)
expectedwarm=[(phase+1,kind,side,phase) for kind in ['sparse','dense'] for phase in [0,1] for side in ['reference','candidate']];ck('warm_order',[(v['round'],v['kind'],v['side'],v['phase']) for v in warm]==expectedwarm)
F=lambda b:Q.from_float(struct.unpack('>d',bytes.fromhex(b))[0]);matrices={}
for f in oracle['fixtures']:
 M=[[Q(0) for _ in range(96)] for _ in range(96)]
 for j in range(96):
  for k in range(f['colptr'][j]-1,f['colptr'][j+1]-1):M[f['rowval'][k]-1][j]=F(f['nzval_bits'][k])
 matrices[(f['kind'],f['phase'])]=(M,f)
residuals=[]
for e in a['endpoints']:
 M,f=matrices[(e['kind'],e['phase'])]
 for direction,rhsname in [('forward','rhs_forward_bits'),('transpose','rhs_transpose_bits')]:
  z=list(map(F,e[direction+'_bits']));b=list(map(F,f[rhsname]));rows=M if direction=='forward' else list(zip(*M))
  residual=[sum((c*x for c,x in zip(row,z)),Q(0))-rhs for row,rhs in zip(rows,b)];norm=max(map(abs,residual));scale=max(Q(1),max(sum(map(abs,row)) for row in rows)*max(map(abs,z)),max(map(abs,b)));bound=Q(64,2**52)*scale
  residuals.append({'label':e['label'],'direction':direction,'residual_inf':str(norm),'bound':str(bound),'all_zero':all(v==0 for v in residual),'passed':norm<=bound})
ck('exact_residual88',len(residuals)==88 and all(v['passed'] for v in residuals));ck('all_controls_equal',all(e['native']['controls']==a['endpoints'][0]['native']['controls'] for e in a['endpoints']));ck('native_status0',all(e['native']['status']==0 for e in a['endpoints']));ck('native_size_unit16',all(e['native']['sizes']['SIZE_OF_UNIT']==16 for e in a['endpoints']))
pairs=[];summary={}
for kind in ['sparse','dense']:
 for rnd in range(1,9):
  ref=next(v for v in meas if v['kind']==kind and v['round']==rnd and v['side']=='reference');cand=next(v for v in meas if v['kind']==kind and v['round']==rnd and v['side']=='candidate')
  er=next(e for e in a['endpoints'] if e['label']==f'round{rnd}_{kind}_reference');ec=next(e for e in a['endpoints'] if e['label']==f'round{rnd}_{kind}_candidate')
  pairs.append({'kind':kind,'round':rnd,'phase':ref['phase'],'seconds_ratio':cand['seconds']/ref['seconds'],'bytes_ratio':cand['bytes']/ref['bytes'],'events_ratio':cand['allocations']/ref['allocations'],'fingerprints_equal':er['fingerprint']==ec['fingerprint'],'outputs_equal':all(er[k]==ec[k] for k in ['forward_bits','transpose_bits'])})
 pp=[v for v in pairs if v['kind']==kind];ref=[v for v in meas if v['kind']==kind and v['side']=='reference'];cand=[v for v in meas if v['kind']==kind and v['side']=='candidate'];rat=[v['seconds_ratio'] for v in pp]
 summary[kind]={'paired_median_ratio':statistics.median(rat),'paired_min':min(rat),'paired_max':max(rat),'paired_mad':statistics.median(abs(x-statistics.median(rat)) for x in rat),'side_median_ratio':statistics.median(v['seconds'] for v in cand)/statistics.median(v['seconds'] for v in ref),'reference_median_seconds':statistics.median(v['seconds'] for v in ref),'candidate_median_seconds':statistics.median(v['seconds'] for v in cand),'reference_bytes':sorted(set(v['bytes'] for v in ref)),'candidate_bytes':sorted(set(v['bytes'] for v in cand)),'reference_events':sorted(set(v['allocations'] for v in ref)),'candidate_events':sorted(set(v['allocations'] for v in cand)),'total_gc_seconds':sum(v['gc_seconds'] for v in ref+cand)}
ck('pairs16_equal_recorded_endpoints',len(pairs)==16 and all(v['fingerprints_equal'] and v['outputs_equal'] for v in pairs));ck('graph3_bounded_observation',len(a['checkpoints'])==3 and all(v['julia_graph_bytes']>0 for v in a['checkpoints']));ck('postexit_groups_absent',json.loads((o/'host-postexit.json').read_text())['matches']==[]);ck('source_test_ci_master_equal',not subprocess.check_output(['git','diff','master','--','src','test','.github']))
result={'checks':checks,'all_passed':all(checks.values()),'residuals':residuals,'nonzero_residual_count':sum(not x['all_zero'] for x in residuals),'pairs':pairs,'summary':summary,'setup_totals':{k:sum(v[k] for v in a['setups']) for k in ['seconds','compile_seconds','bytes','allocations']},'warmup_totals':{k:sum(v[k] for v in warm) for k in ['seconds','compile_seconds','bytes','allocations']},'report_sha256':sha(raw/'report.toml'),'auditor_postexit_sha256':sha(__file__),'auditor_not_launch_pin':str(Path(__file__).resolve()) not in pins['inventory'],'native_retention':'OPEN; these metrics are not a live native allocation/free ledger'}
with (o/'cost-1-audit.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({'gates':len(checks),'passed':sum(checks.values()),'nonzero_residuals':result['nonzero_residual_count'],'summary':summary,'failed':[k for k,v in checks.items() if not v]},indent=2));assert result['all_passed']
