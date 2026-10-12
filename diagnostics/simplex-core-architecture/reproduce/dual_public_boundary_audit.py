from pathlib import Path
from fractions import Fraction as Q
import json,tomllib,hashlib,importlib.util,shutil,sys
sys.dont_write_bytecode=True
root=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=root/'diagnostics/simplex-core-architecture';o=d/'results/S6-AF';b=root/'.superpowers/simplex-core-architecture/S6-AF/qualification-1'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=json.loads((b/'process.json').read_text());pins=json.loads((b/'pins.json').read_text());r=tomllib.loads((b/'report.toml').read_text());log=(b/'run.log').read_text();data=tomllib.loads((d/'results/S6-AE/inputs.toml').read_text());pre=json.loads((o/'preflight.json').read_text());records=r['records'];subjects=[x for x in records if x['mode']!='control'];controls=[x for x in records if x['mode']=='control']
rat=lambda s:Q(s.replace('//','/'));vec=lambda v:list(map(rat,v));B=[vec(row) for row in data['B']];BT=list(map(list,zip(*B)))
mv=lambda A,x:[sum((a*v for a,v in zip(row,x)),Q(0)) for row in A]
primal=[-row[1] for row in B];expected_point=[0,-1,0,0,0]+primal
spec=importlib.util.spec_from_file_location('g',d/'reproduce/guarded_run.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
c={'exit0':p['returncode']==0 and p['reason']=='exit0','pins_unchanged':p['pins_unchanged'] and g.pins_match(pins),'independent_hashes':all(h(Path(k))==v['sha256'] and str(Path(k).resolve())==v['resolved'] for k,v in pins['inventory'].items()),'actual_source':r['source']==str(root/'src/JSimplex.jl'),'test_preserved':r['test_sha256']==pre['test_sha256']==h(root/'test/dual_pivot_consistency_tests.jl'),'input_identity':r['input_sha256']==pre['input_sha256']==h(d/'results/S6-AE/inputs.toml') and r['input']==data,'AE_link':pre['AE_report_sha256']==h(d/'results/S6-AE/components-1-report.toml'),'shared517':len(pre['shared_pins'])==517 and all(h(Path(k))==v['sha256'] for k,v in pre['shared_pins'].items()),'threads':r['julia_threads']==r['blas_threads']==1,'globals':r['globals_preserved'],'cases24':len(records)==24 and len({(x['manager'],x['mode']) for x in records})==24 and len(subjects)==20 and len(controls)==4,'no_errors':all(x['error']=='none' for x in records),'assertions269':'|  269    269' in log and 'Test Failed' not in log and 'Error During Test' not in log}
def expected(mode):
 t=int(mode=='after_refresh')
 return dict(ftran=2+t,prepared=2,ordinary=t,btran=3+t,unit=2,correction=1,cost=t,metadata=2,invalidate=4+2*t,refactor=t,update=0,copy=0,hits=2)
c['complete_attempt_counts']=all(x['counts']==expected(x['mode']) for x in subjects)
c['whole_work']=all(x['kernels']==dict(ftran=expected(x['mode'])['ftran'],btran=expected(x['mode'])['btran'],refactorization=expected(x['mode'])['refactor']) for x in subjects)
c['control_oracle']=all(x['status']=='INFEASIBLE' and x['kernels']==dict(ftran=1,btran=3,refactorization=1) and x['rejected']==0 for x in controls)
c['original_oracle']=all((x['status']==('TIME_LIMIT' if x['mode'] in ['cancelled','after_refresh'] else 'NUMERICAL_ERROR') if x['mode'] not in ['callback_error','numerical_callback_error'] else ('DiagnosticObserverFailure{ErrorException}' in x['result_type'] if x['mode']=='callback_error' else 'DiagnosticObserverFailure{SingularException}' in x['result_type'])) and sum(e['event']=='pivot_rejected' for e in x['events'])==1 for x in subjects)
c['selected_state']=all(all(x['before'][k]==x['after'][k] for k in ['primal','costs','prices','basis','states','iterations']) and x['after']['refactorizations']==x['before']['refactorizations']+int(x['mode'] in ['after_refresh','control']) and not x['after']['rejected_rows'] and not x['after']['rejected_entering'] and x['after']['updates']==0 for x in records)
c['exact_point_basis']=all(vec(x['before']['primal'])==vec(x['after']['primal'])==expected_point and x['after']['basis']==[1,2,3,4] and x['after']['iterations']==0 for x in records)
c['shared_factor']=all(x['factor_identity'] and all(e['same_factor'] for e in x['events']) and any(e['staged'] for e in x['events']) for x in subjects)
c['model_preserved']=all(x['model_preserved'] for x in records)
expected_io={'unit':(vec(data['unit_rhs']),vec(data['exact_rho']),vec(data['declared_rho'])),'prepared':(vec(data['duplicate_rhs']),vec(data['direction']),vec(data['direction'])),'correction':(vec(data['correction_rhs']),vec(data['correction']),vec(data['correction'])),'ordinary':(primal,[0,-1,0,0],[0,-1,0,0]),'cost':([0]*4,[0]*4,[0]*4)}
c['real_forward_outputs']=all((vec(a['rhs']),vec(a['real_output']),vec(a['declared_output']))==expected_io[a['kind']] for x in subjects for a in x['calls'])
c['exact_equations']=all(mv(B if a['kind'] in ['ordinary','prepared'] else BT,vec(a['real_output']))==vec(a['rhs']) for x in subjects for a in x['calls'])
c['unit_dispatch']=all(('_UnitTransposeRHS' in a['rhs_type'])==(x['manager']!='pfi') for x in subjects for a in x['calls'] if a['kind']=='unit')
c['call_order']=all([a['kind'] for a in x['calls']]==['unit','prepared','unit','prepared','correction']+(['ordinary','cost'] if x['mode']=='after_refresh' else []) for x in subjects)
c['correction_before_rejection']=all([e['event'] for e in x['events']].index('correction_attempt')<[e['event'] for e in x['events']].index('pivot_rejected') and sum(e['event']=='correction_attempt' for e in x['events'])==1 for x in subjects)
c['refresh_before_recompute']=all(next(e for e in x['events'] if e['event']=='refactor_pivot')['counts']==dict(expected(x['mode']),ftran=2,ordinary=0,btran=3,cost=0,invalidate=4) for x in subjects if x['mode']=='after_refresh')
c['static_negative_budget']=all(x['negative_counts']==dict(x['counts'],unit=3,btran=x['counts']['btran']+1) and x['negative_counts']!=expected(x['mode']) for x in subjects)
c['policy']=all(all(x['policy'][k]=='false' for k in ['hypersparse','pivot_validation','solve_refinement','recovery','stable_ratio']) and x['policy']['max_refinements']=='3' and x['policy']['max_pivot_candidates']==('8' if x['mode'] in ['control','after_refresh'] else '2' if x['mode']=='cancelled' else '1') and x['policy']['max_recovery_rounds']==('2' if x['mode'] in ['control','after_refresh'] else '0') for x in records)
c['options']=all(x['options']['primal_tolerance']==x['options']['dual_tolerance']=='1.0e-7' and x['options']['zero_tolerance']=='1.0e-12' and x['options']['algorithm']==':dual' and x['options']['pricing']==':dantzig' and x['options']['simplex_strategy']==':legacy' for x in records)
c['user_hashes']=all(h(Path('/home/jspitz/JSimplex.jl')/k)==v for k,v in json.loads(Path('/tmp/jsimplex-main-preserved.json').read_text()).items())
result={'checks':c,'all_passed':all(c.values()),'pin_count':len(pins['inventory']),'scope':'New public-boundary qualification only; original assertion predicates on new fixture and declared outputs, not historical backend/CI cause or general lifecycle/throwing-backend proof.'}
with (o/'qualification-1-audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
for n in ['report.toml','pins.json','process.json','run.log']:shutil.copyfile(b/n,o/('qualification-1-'+n))
shutil.copyfile(d/'reproduce/dual_public_boundary.jl',o/'qualification-1-driver.jl')
print(json.dumps(result,indent=2));assert result['all_passed']
