from pathlib import Path
from fractions import Fraction as Q
import json,tomllib,hashlib,importlib.util,shutil,sys
sys.dont_write_bytecode=True
root=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=root/'diagnostics/simplex-core-architecture';o=d/'results/S6-AE';b=root/'.superpowers/simplex-core-architecture/S6-AE/components-1'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=json.loads((b/'process.json').read_text());pins=json.loads((b/'pins.json').read_text());r=tomllib.loads((b/'report.toml').read_text());log=(b/'run.log').read_text();data=tomllib.loads((o/'inputs.toml').read_text());ad=json.loads((d/'results/S6-AD/exact-contract.json').read_text());records=r['records'];rat=lambda s:Q(s.replace('//','/'));vec=lambda v:list(map(rat,v));B=[vec(row) for row in data['B']]
matvec=lambda A,x:[sum((a*v for a,v in zip(row,x)),Q(0)) for row in A];BT=list(map(list,zip(*B)))
spec=importlib.util.spec_from_file_location('g',d/'reproduce/guarded_run.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
c={'process_exit0':p['returncode']==0 and p['reason']=='exit0','guard_pins':p['pins_unchanged'] and g.pins_match(pins),'independent_hashes':all(h(Path(k))==v['sha256'] and str(Path(k).resolve())==v['resolved'] for k,v in pins['inventory'].items()),'actual_source':r['source']==str(root/'src/JSimplex.jl'),'input_hash':r['input_sha256']==h(o/'inputs.toml'),'AD_link':data['source_sha256']==h(d/'results/S6-AD/exact-contract.json'),'input_data_identity':r['input']==data and all(data[k]==ad['candidate'][k] for k in data if k!='source_sha256'),'threads':r['julia_threads']==r['blas_threads']==1,'globals':r['globals_preserved'] and r['global_precision']==256 and r['global_rounding']=='RoundingMode{:Nearest}()','eight_unique_cases':len(records)==8 and len({(x['manager'],x['mode']) for x in records})==8,'no_errors':all(x['error']=='none' for x in records),'assertions73': '|   73     73' in log and 'Test Failed' not in log and 'Error During Test' not in log}
# Reconstruct actual sparse B; proof is exact over represented input values.
actual=[[Q(0) for j in range(4)] for i in range(4)]
for j in range(4):
 for k in range(r['matrix_colptr'][j]-1,r['matrix_colptr'][j+1]-1):actual[r['matrix_rowval'][k]-1][j]=rat(r['matrix_values'][k])
c['actual_matrix_exact']=actual==B
c['work_entries']=all(x['initial_factorizations']==1 and x['refactors']==(x['mode']=='refactor') and all(x[k]==1 for k in ['unit_btran','prepared_ftran','correction_btran','quality_entries','explicit_invalidations']) for x in records)
c['input_preservation']=all(x['input_preserved'] for x in records)
c['raw_endpoints_exact']=all(vec(x['rho'])==vec(data['exact_rho']) and vec(x['direction'])==vec(data['direction']) and vec(x['correction'])==vec(data['correction']) for x in records)
c['exact_equations']=all(matvec(BT,vec(x['rho']))==vec(data['unit_rhs']) and matvec(B,vec(x['direction']))==vec(data['duplicate_rhs']) and matvec(BT,vec(x['correction']))==vec(data['correction_rhs']) for x in records)
c['native_correction_rhs']=all(not x['quality_isnothing'] and x['quality_finite'] and vec(x['quality_residual'])==vec(data['correction_rhs']) for x in records)
c['prepared_lifecycle']=all(x['updates_before']==x['updates_after']==x['prepared_before']==x['prepared_after_invalidation']==0 and x['prepared_after_ftran']==x['prepared_after_correction']==(x['manager']!='pfi') for x in records)
c['unit_dispatch']=all(('_UnitTransposeRHS' in x['unit_rhs_type'])==(x['manager']!='pfi') for x in records)
c['unchanged_native_policy']=all(all(x['policy'][k]=='false' for k in ['hypersparse','pivot_validation','solve_refinement','recovery','stable_ratio']) and all(x['policy'][k]==v for k,v in {'max_refinements':'3','max_pivot_candidates':'8','max_recovery_rounds':'2','solve_tolerance':repr(float(Q(1,2**44)))}.items()) for x in records)
c['original_options']=all(x['options']['primal_tolerance']==x['options']['dual_tolerance']=='1.0e-7' and x['options']['zero_tolerance']=='1.0e-12' and x['options']['algorithm']==':dual' and x['options']['pricing']==':dantzig' and x['options']['simplex_strategy']==':legacy' for x in records)
paths=set(pins['files'])
for tree in pins['trees']:paths.update(str(x) for x in Path(tree).rglob('*') if x.is_file())
# guard records explicit inputs in its own list in addition to files/trees.
paths.update(pins.get('inputs',[]));c['inventory_membership']=paths==set(pins['inventory'])
pre=json.loads((o/'preflight.json').read_text());c['517_shared_pins']=len(pre['shared_pins'])==517 and all(h(Path(k))==v['sha256'] for k,v in pre['shared_pins'].items())
c['user_hashes']=all(h(Path('/home/jspitz/JSimplex.jl')/k)==v for k,v in json.loads(Path('/tmp/jsimplex-main-preserved.json').read_text()).items())
result={'checks':c,'all_passed':all(c.values()),'pin_count':len(pins['inventory']),'quality_reliable':[x.get('quality_reliable') for x in records],'scope':'New component endpoint, native residual and prepared-destination qualification only; no public recovery/ownership/budget/CI or speedup proof.'}
with (o/'components-1-audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
for n in ['report.toml','pins.json','process.json','run.log']:shutil.copyfile(b/n,o/('components-1-'+n))
shutil.copyfile(d/'reproduce/dual_dyadic_components.jl',o/'components-1-driver.jl')
print(json.dumps(result,indent=2));assert result['all_passed']
