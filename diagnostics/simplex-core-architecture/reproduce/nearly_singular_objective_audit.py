from pathlib import Path
import sys,json,tomllib,hashlib,importlib.util,re,shutil
from fractions import Fraction as F
sys.dont_write_bytecode=True
root=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
base=root/'.superpowers/simplex-core-architecture/S6-N/census-2'
out=root/'diagnostics/simplex-core-architecture/results/S6-N'
r=tomllib.loads((base/'report.toml').read_text());proc=json.loads((base/'process.json').read_text());pins=json.loads((base/'pins.json').read_text());log=(base/'run.log').read_text()
Q=lambda s:F(s.replace('//','/'))
checks={}
checks['four_types_in_original_order']=[x['type'] for x in r['records']]==['Float32','Float64','BigFloat','Rational{BigInt}']
checks['actual_source']=r['source']==str(root/'src/JSimplex.jl')
checks['source_test_pin']=r['test_sha256']==hashlib.sha256((root/'test/solver_tests.jl').read_bytes()).hexdigest()
checks['guard_complete']=proc['returncode'] in [0,1] and proc['reason']=='exit'+str(proc['returncode']) and proc['pins_unchanged']
s=importlib.util.spec_from_file_location('g',root/'diagnostics/simplex-core-architecture/reproduce/guarded_run.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
checks['pins_guard']=g.pins_match(pins)
checks['pins_independent']=all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items())
checks['single_threads']=r['julia_threads']==r['blas_threads']==1
checks['unchanged_oracle']=r['oracle_assertions_unchanged'] and r['default_public_solve_unchanged']
checks['globals_preserved']=r['globals_restored'] and all(x['globals_unchanged_after_solve'] for x in r['records'])
checks['models_preserved']=all(x['model_unchanged'] and x['model_before']==x['model_after'] for x in r['records'])
checks['default_options']=all(x['options']['algorithm']==':dual' and x['options']['presolve']=='true' and x['options']['scaling']==':auto' and x['options']['basis_refactorization']==':native' for x in r['records'])
checks['matrix_exact']=all([Q(v['exact']) for v in x['model_before']['matrix']]==[F(1,2**20)]*3+[F(1,2**20)+F(1,2**43)] for x in r['records'])
checks['strict_proof']=all(Q(x['determinant_exact'])==F(1,2**63) and Q(x['delta_exact'])==F(1,2**43) and Q(x['strict_optimum_exact'])==-2**44 and list(map(Q,x['strict_primal_exact']))==[-2**44-2**20,2**44] and list(map(Q,x['strict_rows_exact']))==[-1,1] and all(Q(v)==0 for v in x['dual_stationarity_exact']) for x in r['records'])
checks['no_invalid_status_publication']=all(x['status'] in ['OPTIMAL','NUMERICAL_ERROR'] and x['has_primal']==x['has_objective']==(x['status']=='OPTIMAL') for x in r['records'])
optimal=[x for x in r['records'] if x['has_primal']]
checks['objective_matches_primal']=all(x['objective_matches_primal_exact'] and Q(x['objective']['exact'])==Q(x['objective_from_primal_exact'])==-Q(x['primal'][1]['exact']) for x in optimal)
checks['exact_rows_recomputed']=all(list(map(Q,x['rows_exact']))==[F(1,2**20)*(Q(x['primal'][0]['exact'])+Q(x['primal'][1]['exact'])),F(1,2**20)*(Q(x['primal'][0]['exact'])+Q(x['primal'][1]['exact']))+F(1,2**43)*Q(x['primal'][1]['exact'])] for x in optimal)
checks['original_feasibility']=all(x['original_primal_certificate'] and x['tolerance_feasible_exact'] and all(Q(v)<=Q(x['tolerances_exact']['primal_tolerance']) for v in x['row_violations_exact']) for x in optimal)
checks['gap_residual_identity']=all(Q(x['objective_gap_exact'])==2**43*(Q(x['rows_exact'][0])+1-(Q(x['rows_exact'][1])-1)) for x in optimal)
checks['analytic_witness']=all(x['analytic_complementarity_within_tolerance'] and x['analytic_witness_certificate'] for x in optimal)
checks['tolerance_envelope']=all(Q(x['tolerance_objective_lower_exact'])==-2**44*(1+Q(x['tolerances_exact']['primal_tolerance'])) and Q(x['objective']['exact'])>=Q(x['tolerance_objective_lower_exact']) for x in optimal)
checks['rational_exact']=all(x['status']=='OPTIMAL' and Q(x['objective_gap_exact'])==0 and Q(x['tolerances_exact']['primal_tolerance'])==0 for x in r['records'] if x['type']=='Rational{BigInt}')
checks['original_failure_preserved']='Test Failed' in log and 'result.objective_value == -(T(big(2) ^ 44))' in log and proc['returncode']==1 and 'Error During Test' not in log
summary=[{k:x[k] for k in ['type','status','message','iterations','refactorizations','has_primal','has_objective','objective_gap_exact','rows_exact','row_violations_exact','analytic_witness_certificate'] if k in x} for x in r['records']]
audit={'checks':checks,'all_passed':all(checks.values()),'pin_count':len(pins['inventory']),'summary':summary,'scope':'Local unchanged public oracle, postsolve analytic witness only; no runtime dual/basis trace, x64/full-suite or performance proof.'}
with (out/'census-2-audit.json').open('x') as f:json.dump(audit,f,indent=2);f.write('\n')
for name in ['report.toml','process.json','run.log','pins.json']:shutil.copyfile(base/name,out/('census-2-'+name))
shutil.copyfile(root/'diagnostics/simplex-core-architecture/reproduce/nearly_singular_objective_census.jl',out/'census-2-driver.jl')
print(json.dumps(audit,indent=2))
