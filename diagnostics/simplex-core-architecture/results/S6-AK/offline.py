from pathlib import Path
from fractions import Fraction as F
import hashlib,json,math,struct,subprocess
r=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');b=r/'diagnostics/simplex-core-architecture';o=b/'results/S6-AK';o.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=r)
inv=json.loads((b/'results/S6-A/ci-inventory-1.json').read_text());run=next(x for x in inv['records'] if x['run']==38142752357); es=[x for x in run['entries'] if x['file']=='test/primal_perturbation_integration_tests.jl']; assert [x['line'] for x in es]==[187,188,189]
raw=Path(inv['raw_location'])/'38142752357-failed.log';assert sha(raw)==inv['raw_manifest'][raw.name]
(o/'historical-context.txt').write_text('\n'.join(raw.read_text().splitlines()[1427:1464])+'\n')
(o/'inventory-entries.json').write_text(json.dumps(es,indent=2)+'\n')
text=es[1]['details'][1];events='[:refactor_initial, :refactor_other, :perturbation, :pricing, :pivot_proposed, :pivot_completed, :pricing, :checkpoint]'
checks={'three_old_only_failures':len(es)==3 and not any(e['file'].endswith('primal_perturbation_integration_tests.jl') for e in inv['records'][0]['entries']), 'raw_hash':True,'event_vector8_next9':events+', 9, nothing, false' in text,'historical_point_basis_states':'Basis([2], JSimplex.VariableState[JSimplex.AT_LOWER, JSimplex.BASIC]), [-9.0e-7, -9.0e-7], [1.0, 0.0]' in text,'zero_progress_offsets':'JSimplex.Scaling{Float64}([1.0], [1.0]), 0, 0,' in text,'native_policy_printed':'NumericalPolicy{Float64}(5.684341886080802e-14, 1.4901161193847656e-8, 3, 8, 2, 64, 512, 1073741824, 8, false, false, false, false, false, false, false, false, true' in text,'current_test_equal_historical':(r/'test/primal_perturbation_integration_tests.jl').read_bytes()==git('show','b720674:test/primal_perturbation_integration_tests.jl')}
t=1e-7; cap=512*t; margin=min(cap,t*9.0*1.0*1.0); lower=-margin;point=[lower,lower];zero=F(0)
checks.update({'represented_margin_matches_printed':lower==-9e-7,'margin_greater_than_tolerance':F(margin)>F(t),'margin_within_cap':F(margin)<=F(cap),'working_equation_exact':F(point[0])-F(point[1])==0,'working_structural_lower_exact':F(point[0])==F(lower),'original_lower_violation_gt_tolerance':-F(point[0])>F(t),'basic_free_row_no_bound_violation':True,'driver_nonbasic_price_nonnegative':F(1)>-F(t),'basis_FTRAN_exact':-F(point[1])==-F(point[0]),'basis_BTRAN_exact':-F(0)==0,'restored_point_exact_zero':F(0)-F(0)==0,'iteration_count_below_limit':1<20})
# The two explicit source/semantic declarations above describe the captured free
# basic row and AT_LOWER nonbasic price; they are not calls to production predicates.
paths=['src/simplex_driver.jl','src/simplex.jl','src/primal_simplex.jl','src/dual_simplex.jl','src/native_cleanup_recovery.jl','src/simplex_recovery.jl','src/simplex_numerics.jl','src/simplex_diagnostics.jl','src/simplex_pricing.jl','src/legacy_primal_point.jl','src/solver.jl','src/simplex_perturbation.jl','test/primal_perturbation_integration_tests.jl','test/primal_perturbation_tests.jl']
pins={p:sha(r/p) for p in paths};historical={p:sha(r/p)==hashlib.sha256(git('show','b720674:'+p)).hexdigest() for p in paths}
checks['all_contract_sources_except_known_S5C_restore_equal_historical']=all(v for p,v in historical.items() if p!='src/simplex_perturbation.jl')
checks['all_tracked_source_test_CI_equal_master']=all((r/p).read_bytes()==git('show','master:'+p) for p in git('ls-files','src','test','.github/workflows').decode().splitlines())
for p in git('ls-files','src','test','.github/workflows').decode().splitlines():pins[p]=sha(r/p)
for p in ['results/S6-A/ci-inventory-1.json','results/S6-AJ/coverage.json','results/S6-AJ/input-hashes.json','results/S5-C/focused-1-audit.json','results/S5-C/focused-1-run.log']:
 pins['diagnostics/simplex-core-architecture/'+p]=sha(b/p)
users=json.loads((b/'results/S6-AJ/user-hashes.json').read_text());checks['users_unchanged']=all(sha(Path(p))==v for p,v in users.items())
assert all(checks.values()),checks
values={n:{'binary64_hex':v.hex(),'uint64':struct.pack('>d',v).hex(),'rational':str(F(v))} for n,v in [('tolerance',t),('cap',cap),('margin',margin),('shifted_lower',lower)]}
res={'checks':checks,'values':values,'historical_source_matches':historical,'historical_events':events,'captured_start_ns_hex':'0x000004a67c5816f9','start_ns_alone_is_not_elapsed':True,'source_declarations':['basic_free_row_no_bound_violation is a model/state declaration, not production predicate execution'],'scope':'Python exact arithmetic on printed binary64 values, plus source/hash checks; no Julia or historical parser/auditor rerun. No captured run.status/message or monotonic return timestamp.'}
for n,d in [('analysis.json',res),('input-hashes.json',pins),('user-hashes.json',users)]: (o/n).write_text(json.dumps(d,indent=2)+'\n')
(o/'offline.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({'checks':len(checks),'hashes':len(pins),'historical_contract_source_matches':sum(historical.values()),'values':values}))
