"""S6-AN exclusive offline audit. Never rerun after acceptance."""
from pathlib import Path
from fractions import Fraction as Q
import json,tomllib,hashlib,struct,shutil,re
r=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=r/'diagnostics/simplex-core-architecture';o=d/'results/S6-AN';b=r/'.superpowers/simplex-core-architecture/S6-AN/qualification-1'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
x=tomllib.loads((b/'report.toml').read_text());p=json.loads((b/'process.json').read_text());pins=json.loads((b/'pins.json').read_text());pre=json.loads((o/'preflight.json').read_text());host=json.loads((o/'host-after.json').read_text());log=(b/'run.log').read_text();al=tomllib.loads((d/'results/S6-AL/provenance-1-report.toml').read_text());driver=(d/'reproduce/native_cleanup_entry_interruption.jl').read_text()
q=lambda v:Q(v['exact'].replace('//','/'))
bits=[]
def walk(v):
 if isinstance(v,dict):
  if set(v)=={'exact','bits'}:bits.append(struct.pack('>d',float(q(v))).hex()==v['bits'])
  else:
   for z in v.values():walk(z)
 elif isinstance(v,list):
  for z in v:walk(z)
walk(x)
checks={
 'normal_exit':p['returncode']==0 and p['reason']=='exit0',
 'no_logged_test_failure':'Test Failed' not in log and 'Error During Test' not in log,
 'runtime_error_accounted':x['metadata']['exception']=='none' and 'metadata["exception"]=sprint(showerror,exception)' in driver,
 'pins_independent':p['pins_unchanged'] and all(h(Path(k))==v['sha256'] and str(Path(k).resolve())==v['resolved'] for k,v in pins['inventory'].items()),
 'AL_shared_pins':len(pre['shared_AL_pins'])==628 and all(h(Path(k))==v['sha256'] for k,v in pre['shared_AL_pins'].items()),
 'source_and_users':all(h(r/k)==v for k,v in pre['source_hashes'].items()) and all(h(Path(k))==v for k,v in pre['user_hashes'].items()),
 'actual_driver':h(d/'reproduce/native_cleanup_entry_interruption.jl')==pre['driver_sha256'] and x['metadata']['source']==str(r/'src/JSimplex.jl'),
 'actual_helper':x['metadata']['helper_sha256']==pre['helper_hashes']['shifted_primal_workspace'] and x['metadata']['monitor_sha256']==pre['helper_hashes']['primal_stalled_monitor'],
 'processes_absent':host['boot_id']==p['runner']['boot_id']==p['child']['boot_id'] and not host['julia'] and not any(z['present'] for z in host['processes']),
 'two_cases':set(x['cases'])=={'stop','throw'},
 'threads_globals':x['metadata']['julia_threads']==x['metadata']['blas_threads']==1 and x['metadata']['globals_preserved'] and x['metadata']['globals_before']==al['metadata']['globals_before'],
 'actual_bits':len(bits)>200 and all(bits),
 'original_six_unchanged':(o/'original-target.jl.txt').read_bytes()==(d/'results/S6-AL/original-target.jl.txt').read_bytes() and (o/'original-target.jl.txt').read_text().count('@test ')==6,
}
summary={}
fields='point costs prices rho lower upper basis states perturbed journal model options policy start_ns iteration_offset refactorization_offset iterations refactorizations row_scaling column_scaling factor_type observer_absent'.split()
for mode,c in x['cases'].items():
 s=c['snapshots'];a=s['setup'];i=s['initial'];before=s['before_driver'];after=s['final'];pay=c['payloads'];t={k:int(v) for k,v in c['times'].items()};start=int(a['start_ns']);kd=lambda u,v:{k:v['kernel_calls'][k]-n for k,n in u['kernel_calls'].items()};nz=lambda v:{k:n for k,n in v.items() if n};elapsed=[t['driver_before']-start,t['driver_after']-start];classification='entry_expired' if elapsed[0]>=30_000_000_000 else 'excluded_within_bracket' if elapsed[1]<30_000_000_000 else 'straddling_ambiguous'
 def add(k,v):checks[mode+'_'+k]=v
 add('one_each_entry',c['entries']==dict(helper=1,initial_optimizer=1,budget_constructor=1,run_from_basis=1))
 add('one_callback',pay['callback_calls']==1)
 add('initial_OPTIMAL',pay['initial']['status']=='OPTIMAL')
 add('initial_work',nz(kd(a,i))==dict(ftran=2,btran=3,pricing=2) and i['kernel_calls']==before['kernel_calls'])
 add('driver_work',not any(kd(before,after).values()))
 add('selected_state_preserved',all(before[k]==after[k] for k in fields))
 add('AL_initial_selected_match',all(i[k]==al['snapshots']['initial'][k] for k in 'point costs prices rho lower upper basis states perturbed model options policy iteration_offset refactorization_offset iterations refactorizations row_scaling column_scaling factor_type observer_absent'.split()))
 add('options_policies_match_AL',all(s[k]['options']==al['snapshots'][k]['options'] and s[k]['policy']==al['snapshots'][k]['policy'] for k in s))
 add('real_PFI_no_observer',all(z['observer_absent'] and 'PFIFactorization' in z['factor_type'] for z in s.values()))
 add('model_preserved',all(z['model']==a['model'] for z in s.values()))
 add('owned_active_journal',all(z['journal']['owner_match'] and z['journal']['bounds']['active'] and z['journal']['bounds']['active_lower']==z['lower'] and z['journal']['bounds']['active_upper']==z['upper'] for z in s.values()))
 add('exact_working_equation',all(q(z['point'][0])-q(z['point'][1])==0 for z in s.values()))
 add('exact_initial_margin',q(before['point'][0])==-9*q(a['options']['primal_tolerance']) and before['point'][0]['bits']=='beae32f0ee144531')
 add('clock_and_budget',all(int(z['start_ns'])==start for z in s.values()) and pay['budget_before']==pay['budget_after'] and int(pay['budget_after']['start_ns'])==start and pay['budget_after']['iterations']==after['iterations']==1 and pay['budget_after']['refactorizations']==after['refactorizations']==1)
 add('monotonic_brackets',t['helper_before']<=start<=t['helper_after']<=t['initial_before']<=t['initial_after']<=t['driver_before']<=t['driver_after'])
 add('setup_not_counted',not a['kernel_timing'] and not any(a['kernel_calls'].values()) and a['refactorizations']==1 and all(s[k]['kernel_timing'] for k in ['initial','before_driver','final']))
 expected=['checkpoint'] if mode=='stop' else []
 add('events_exact',after['event_ring']==before['event_ring']+expected and after['next_event']==before['next_event']+len(expected) and all(after['event_counts'][k]-v==(1 if mode=='stop' and k=='checkpoint' else 0) for k,v in before['event_counts'].items()))
 if mode=='stop':
  run=pay['run'];add('result_exact',run['status']=='TIME_LIMIT' and run['message']=='time limit reached during feasibility recovery' and run['primal']==run['objective']==run['basis']=='nothing' and not pay['caught']['same_sentinel'] and pay['caught']['message']=='none')
 else:add('exception_identity_no_result',pay['caught']['same_sentinel'] and pay['caught']['type']=='SingularException' and pay['run']=='nothing')
 summary[mode]={'initial_work':nz(kd(a,i)),'driver_work':nz(kd(before,after)),'driver_elapsed_ns':elapsed,'deadline_class':classification,'callback_calls':pay['callback_calls'],'journal_aliases':{k:before['journal'][k] for k in ['lower_alias','upper_alias']},'result':pay['run'],'caught':pay['caught']}
result=dict(checks=checks,all_passed=all(checks.values()),pin_count=len(pins['inventory']),actual_bit_checks=len(bits),cases=summary,scope='Two declared callback entry interruptions only; bracket classification is not private clock capture or historical cause. Zero driver kernels is not zero total work; disabled setup counters are not zero setup work. Captures consume shared budget.')
with (o/'qualification-1-audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
for name in ['report.toml','process.json','pins.json','run.log']:shutil.copyfile(b/name,o/('qualification-1-'+name))
shutil.copyfile(d/'reproduce/native_cleanup_entry_interruption.jl',o/'qualification-1-driver.jl')
print(json.dumps({'all_passed':result['all_passed'],'checks':len(checks),'false':[k for k,v in checks.items() if not v],'pins':result['pin_count'],'bits':len(bits),'cases':summary},indent=2));assert result['all_passed']
