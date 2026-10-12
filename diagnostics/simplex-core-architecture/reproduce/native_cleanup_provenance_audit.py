"""Exclusive offline audit for S6-AL provenance-1. Never rerun on accepted evidence."""
from pathlib import Path
from fractions import Fraction as Q
import hashlib,json,tomllib,struct,shutil,re,sys,importlib.util
sys.dont_write_bytecode=True
root=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=root/'diagnostics/simplex-core-architecture';o=d/'results/S6-AL';b=root/'.superpowers/simplex-core-architecture/S6-AL/provenance-1'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=tomllib.loads((b/'report.toml').read_text());p=json.loads((b/'process.json').read_text());pins=json.loads((b/'pins.json').read_text());pre=json.loads((o/'preflight.json').read_text());host=json.loads((o/'host-after.json').read_text());log=(b/'run.log').read_text()
s=r['snapshots'];a=s['setup'];i=s['initial'];c=s['before_driver'];f=s['final'];m=r['metadata'];times={k:int(v) for k,v in r['times'].items()};start=int(a['start_ns']);pay=r['payloads'];run=pay['run']
q=lambda x:Q(x['exact'].replace('//','/'));v=lambda x:list(map(q,x))
bits=[]
def checkbits(x):
 if isinstance(x,dict):
  if set(x)=={'bits','exact'}:bits.append(struct.pack('>d',float(q(x))).hex()==x['bits'])
  else:
   for y in x.values():checkbits(y)
 elif isinstance(x,list):
  for y in x:checkbits(y)
checkbits(r)
delta=lambda before,after:{k:after['kernel_calls'][k]-before['kernel_calls'][k] for k in before['kernel_calls']}
initialwork=delta(a,i);cleanupwork=delta(c,f)
nonzero=lambda x:{k:v for k,v in x.items() if v}
intervals={name:{'before_elapsed_ns':times[name+'_before']-start,'after_elapsed_ns':times[name+'_after']-start,'duration_ns':times[name+'_after']-times[name+'_before']} for name in ['helper','setup_capture','initial','initial_capture','driver_capture','driver','final_capture']}
for name,x in intervals.items():x['deadline_class']='entry_expired' if x['before_elapsed_ns']>=30_000_000_000 else 'excluded_within_bracket' if x['after_elapsed_ns']<30_000_000_000 else 'straddling_ambiguous'
policy_changes={k:[a['policy'][k],c['policy'][k]] for k in a['policy'] if a['policy'][k]!=c['policy'][k]}
adaptive=['adaptive_primal_perturbation','adaptive_dual_perturbation','adaptive_stalling','adaptive_pricing','adaptive_refactor']
expected_changes={k:[True,False] for k in adaptive};expected_changes['refactor_timing']=[False,True]
opt=a['options'];tol=q(opt['primal_tolerance']);margin=-q(c['point'][0]);target=(o/'original-target.jl.txt').read_text();driver=(d/'reproduce/native_cleanup_provenance.jl').read_text()
spec=importlib.util.spec_from_file_location('guard',d/'reproduce/guarded_run.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
checks={
 'exit0':p['returncode']==0 and p['reason']=='exit0',
 'seven_original_assertions':bool(re.search(r'\|\s+7\s+7\s',log)) and 'Test Failed' not in log and 'Error During Test' not in log and target.count('@test ')==6,
 'actual_exception_accounting':m['exception']=='none' and 'metadata["exception"]=sprint(showerror,exception)' in driver,
 'guard_pins':p['pins_unchanged'] and g.pins_match(pins),
 'independent_pins':all(h(Path(k))==x['sha256'] and str(Path(k).resolve())==x['resolved'] for k,x in pins['inventory'].items()),
 'AG627_shared':len(pre['shared_AG_pins'])==627 and all(h(Path(k))==x['sha256'] for k,x in pre['shared_AG_pins'].items()),
 'contract_source_hashes':all(h(root/k)==x for k,x in pre['source_hashes'].items()),
 'actual_driver_source':h(d/'reproduce/native_cleanup_provenance.jl')==pre['driver_sha256'] and m['source']==str(root/'src/JSimplex.jl'),
 'actual_helper_source':m['helper_sha256']==pre['helper_hashes']['shifted_primal_workspace'] and m['monitor_sha256']==pre['helper_hashes']['primal_stalled_monitor'],
 'processes_gone_same_boot':host['boot_id']==p['runner']['boot_id']==p['child']['boot_id'] and not host['julia'] and not any(x['present'] for x in host['processes']),
 'one_lifecycle':r['entries']==dict(helper=1,initial_optimizer=1,budget_constructor=1,run_from_basis=1),
 'threads_globals':m['julia_threads']==m['blas_threads']==1 and m['globals_preserved'] and m['globals_before']=='(256, RoundingMode{:Nearest}(), RoundingMode{:Nearest}(), false)',
 'PFI_no_observer':all('PFIFactorization' in x['factor_type'] and x['observer_absent'] for x in s.values()),
 'model_owned_preserved':all(x['model']==a['model'] for x in s.values()) and a['model']['colptr']==[1,2] and a['model']['rowval']==[1] and v(a['model']['nzval'])==v(a['model']['objective'])==[1] and q(a['model']['column_lower'][0]['value'])==0 and not a['model']['column_upper'][0]['finite'] and not a['model']['row_lower'][0]['finite'] and not a['model']['row_upper'][0]['finite'],
 'options_same_defaults':all(x['options']==opt for x in s.values()) and opt['basis_update']=='pfi' and opt['basis_refactorization']=='native' and opt['simplex_strategy']=='legacy' and opt['algorithm']=='primal' and opt['pricing']=='steepest_edge' and opt['iteration_limit']==20 and q(opt['time_limit'])==30 and tol==Q(1e-7) and q(opt['dual_tolerance'])==Q(1e-7) and q(opt['zero_tolerance'])==Q(1e-12),
 'policies_scoped_replacement':a['policy']==i['policy'] and c['policy']==f['policy'] and policy_changes==expected_changes and not c['policy']['feasibility_recovery'] and not c['policy']['recovery'] and not c['policy']['solve_refinement'] and not c['policy']['precision_boosting'],
 'clock_budget_preserved':all(int(x['start_ns'])==start and x['iteration_offset']==x['refactorization_offset']==0 for x in s.values()) and pay['budget_before']==pay['budget_after'] and int(pay['budget_before']['start_ns'])==start and q(pay['budget_before']['time_limit_seconds'])==30 and pay['budget_before']['iteration_limit']==20,
 'monotonic_brackets':all(x['duration_ns']>=0 for x in intervals.values()) and times['helper_before']<=start<=times['helper_after']<=times['setup_capture_before']<=times['setup_capture_after']<=times['initial_before']<=times['initial_after']<=times['initial_capture_before']<=times['initial_capture_after']<=times['driver_capture_before']<=times['driver_capture_after']<=times['driver_before']<=times['driver_after']<=times['final_capture_before']<=times['final_capture_after'],
 'new_driver_deadline_excluded':intervals['driver']['deadline_class']=='excluded_within_bracket',
 'actual_bits':len(bits)>100 and all(bits),
 'same_unit_scaling':all(v(x['row_scaling'])==v(x['column_scaling'])==[1] for x in s.values()),
 'owned_journal_before':all(x['journal']['owner_match'] and x['journal']['cost_length_match'] and not x['journal']['active'] and x['journal']['bounds']['active'] and x['journal']['bounds']['active_lower']==x['lower'] for x in [a,i,c]),
 'initial_exact_shift':margin==9*tol and c['point'][0]['bits']=='beae32f0ee144531' and i['point']==c['point'] and v(c['point'])==[-margin,-margin] and q(c['lower'][0]['value'])==-margin and c['basis']==[2] and c['states']==['AT_LOWER','BASIC'] and margin>tol,
 'exact_working_equations':all(v(x['point'])[0]-v(x['point'])[1]==0 for x in s.values()),
 'original_predicates_recorded':pay['initial']['status']=='OPTIMAL' and run['status']=='OPTIMAL' and v(run['primal'])==[0] and f['lower']==a['journal']['bounds']['original_lower'] and f['upper']==a['journal']['bounds']['original_upper'] and f['journal']=='nothing' and not f['policy']['feasibility_recovery'],
 'original_point_publication':v(f['point'])==[0,0] and q(run['objective'])==0 and run['basis']['indices']==f['basis']==[2] and run['basis']['states']==f['states']==['AT_LOWER','BASIC'] and not f['perturbed'],
 'timing_only_after_setup':not a['kernel_timing'] and all(x['kernel_timing'] for x in [i,c,f]) and not any(a['kernel_calls'].values()) and a['refactorizations']==1 and a['event_ring']==['refactor_initial','refactor_other','perturbation'],
 'observed_initial_work':nonzero(initialwork)==dict(ftran=2,btran=3,pricing=2) and i['kernel_calls']==c['kernel_calls'],
 'observed_cleanup_work':nonzero(cleanupwork)==dict(ftran=2,btran=2) and i['iterations']==c['iterations']==f['iterations']==run['iterations']==1 and i['refactorizations']==c['refactorizations']==f['refactorizations']==run['refactorizations']==1,
 'ordered_restore_certification':f['event_ring']==c['event_ring']+['restore_perturbations','pricing_phase_reset','phase_cleanup','certification'] and f['event_counts']['certification_failed']==0 and f['event_counts']['checkpoint']==0 and f['next_event']==len(f['event_ring'])+1,
 'user_hashes':all(h(Path(k))==v for k,v in pre['user_hashes'].items())}
result={'checks':checks,'all_passed':all(checks.values()),'pin_count':len(pins['inventory']),'represented_float_checks':len(bits),'intervals':intervals,'initial_kernel_delta':nonzero(initialwork),'cleanup_kernel_delta':nonzero(cleanupwork),'policy_changes':policy_changes,'exact_point_before':str(-margin),'exact_point_after':'0','scope':'One new local instrumented lifecycle. Timings include compilation and shared-budget capture overhead. No historical elapsed/status/CI cause or instrumentation neutrality proof. Setup zero disabled counters are not zero work.'}
with (o/'provenance-1-audit.json').open('x') as io:json.dump(result,io,indent=2);io.write('\n')
for name in ['report.toml','process.json','pins.json','run.log']:shutil.copyfile(b/name,o/('provenance-1-'+name))
shutil.copyfile(d/'reproduce/native_cleanup_provenance.jl',o/'provenance-1-driver.jl')
print(json.dumps(result,indent=2));assert result['all_passed']
