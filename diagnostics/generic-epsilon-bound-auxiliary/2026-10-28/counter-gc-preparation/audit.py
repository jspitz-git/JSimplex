from common import *
import re,tomllib,statistics as st,math
F={'seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds'}
G={'allocd','malloc','realloc','poolalloc','bigalloc','freecall','total_time','pause','full_sweep'}
def num(x):return type(x) in (int,float) and math.isfinite(x)
def cost(x,raw=False):
 need(set(x)==F|({'gc_raw'} if raw else set()),'complete cost schema')
 need(all(num(x[k]) and x[k]>=0 for k in F),'finite nonnegative cost')
 need(type(x['bytes']) is int and type(x['events']) is int,'integer counters')
 if raw:
  z=x['gc_raw'];need(set(z)==G and all(type(v) is int for v in z.values()),'all exact integer GC fields')
  need(z['allocd']==x['bytes'] and sum(z[k] for k in ['malloc','realloc','poolalloc','bigalloc'])==x['events'],'GCcounter identity')
def sample(x):
 need(set(x)==F|{'result','capture_preparation'},'UPR sample fields');cost({k:x[k] for k in F});cost(x['capture_preparation']);need(type(x['result']) is float and math.isfinite(x['result']),'scalar metric checksum')
def main():
 c=read('contract.json');p=read('output/process.json');s=read('supervisor.json');log=(D/'output/run.log').read_text();exitcode=p['returncode'];need(exitcode in [0,1] and p['pins_unchanged'] is True,'completed Test and pins')
 need(s['returncode']==(0 if exitcode==0 else 1) and s['accepted'] is (exitcode==0) and not s['soft_timeout'] and not s['hard_timeout'] and 'cleanup_error' not in s and s['elapsed_seconds']<=900,'truthful diagnostic supervisor')
 if exitcode==0:need(read('completed.json')['accepted'] is True and read('completed.json')['elapsed_shared_seconds']<=900,'successful completion clock')
 else:need(not (D/'completed.json').exists(),'failed Test never accepted')
 need(p['command']==c['command']==read('invocation.json')['Julia_command'] and p['pins_sha256']==sha(D/'pins.json'),'exact command/pins')
 gate=read('output/gate.json');cur=read('output/current.json');permit=read('output/permit.json');need(gate['identity']==p['child']==cur['child'] and gate['parent']==p['runner']==cur['runner']==s['guard_identity'],'entry process identities')
 need(gate['command']==cur['command']==permit['command']==c['command'] and gate['parent_death_signal']==9 and gate['current_sha256']==sha(D/'output/current.json')==permit['current_sha256'] and gate['permit_sha256']==sha(D/'output/permit.json'),'entry links')
 need(sha(D/'output/pins.json')==sha(D/'pins.json'),'copied pins');r=read('reservation.json');need(r['guard_deadline']==r['started_monotonic']+892 and r['outer_deadline']==r['started_monotonic']+900,'common clocks')
 need('COUNTER_SOURCE '+str(M/'src/JSimplex.jl') in log,'actual source marker');need(re.findall(r'^INCLUDING (.*)$',log,re.M)==c['files'],'three ordered wholefiles')
 finished=re.findall(r'^FILE_FINISHED (.*) elapsed_seconds=(\S+)$',log,re.M);need([x[0] for x in finished]==c['files'] and all(num(float(x[1])) and float(x[1])>=0 for x in finished),'all files finished with prep-inclusive clocks')
 need('Error During Test' not in log and 'Test Broken' not in log,'no numerical/load/format errors')
 blocks=re.findall(r'^COUNTER_CAPTURE_BEGIN (UPR|DUAL)\n(.*?)^COUNTER_CAPTURE_END \1$',log,re.M|re.S);need(len(blocks)==4 and log.count('COUNTER_CAPTURE_BEGIN ')==log.count('COUNTER_CAPTURE_END ')==4,'exact complete serialization blocks')
 records=[tomllib.loads(v) for k,v in blocks];need([x['kind'] for x in records]==['UPR','UPR','DUAL','DUAL'],'capture order')
 locations=[];results=[]
 changes=read('source-inverse.json')['changes'];lines={x['file']:x['gate_line'] for x in changes}
 for j,x in enumerate(records):
  need(x['type']=='Rational{BigInt}','named type')
  if x['kind']=='UPR':
   need(set(x)=={'kind','type','scope','arm','n','density','shape','mode','gc_preparation','before','after','events_predicate','bytes_predicate'},'UPR fields')
   need(x['scope']==['residual','outer'][j] and x['arm']=='C' and type(x['n']) is int and x['n']==64 and (x['density'],x['shape'],x['mode'])==('sparse','mixed','unit'),'exact UPR case')
   cost(x['gc_preparation']);need(x['gc_preparation']['gc_seconds']>0,'fullGC preparation observed outside window')
   a,b=x['before'],x['after'];need(len(a)==len(b)==3,'three UPR pairs')
   for z in a+b:sample(z);need(z['compile_seconds']==z['recompile_seconds']==0,'UPR compilezero')
   need(all(v['result']==w['result'] for v,w in zip(a,b)),'UPR typed results')
   ev=all(w['events']<v['events'] for v,w in zip(a,b));by=st.median(w['bytes'] for w in b)<st.median(v['bytes'] for v in a)
   need(type(x['events_predicate']) is bool and type(x['bytes_predicate']) is bool and x['events_predicate']==ev and x['bytes_predicate']==by,'independent UPR predicates')
   passed=ev and by;key=x['scope'];location=[str(D/'generic_unit_perturb_residual_tests.jl'),lines['generic_unit_perturb_residual_tests.jl']]
  else:
   need(set(x)=={'kind','type','scope','pattern','other','expect_saving','batch_size','gc_preparation','before','after','records','fixture','snapshot','warmup','wrapper_warmup','wrapper','per_pair_bytes_predicate','per_pair_events_predicate'},'DUAL fields')
   need(x['scope']=='update' and x['pattern']==['lower','free'][j-2] and x['other']=='candidate' and x['expect_saving'] is True and type(x['batch_size']) is int and x['batch_size']==8,'exact DUAL case')
   cost(x['gc_preparation'],True);need(x['gc_preparation']['gc_raw']['full_sweep']>=1 and x['gc_preparation']['gc_seconds']>0,'explicit fullGC preparation recorded')
   a,b=x['before'],x['after'];need(len(a)==len(b)==3 and all(type(y) is int and y>=0 for z in a+b for y in z) and all(len(z)==2 for z in a+b),'typed DUAL arrays')
   rr=x['records'];need(len(rr)==6,'six DUAL records')
   for k,z in enumerate(rr):
    pair=k//2+1;arms=['original','candidate'] if pair%2 else ['candidate','original'];need(z['round']==pair and type(z['round']) is int and z['method']==arms[k%2] and type(z['sink']) is int and type(z['calls']) is int and z['calls']==8,'DUAL ordering/sink/budget')
    need(set(z)==F|{'gc_raw','sink','calls','method','round','reset'},'DUAL record fields');cost({q:z[q] for q in F|{'gc_raw'}},True);cost(z['reset'],True);need(z['compile_seconds']==z['recompile_seconds']==0,'DUAL compilezero')
    need([z['bytes'],z['events']]==(a if z['method']=='original' else b)[pair-1],'DUAL tuple/record identity')
   need(all(rr[k]['sink']==rr[k+1]['sink'] for k in range(0,6,2)),'DUAL result checksums')
   for name in ['fixture','snapshot','warmup','wrapper_warmup']:cost(x[name],True)
   w=x['wrapper'];need(set(w)==F|{'gc_raw','sink','calls'},'wrapper fields');cost({q:w[q] for q in F|{'gc_raw'}},True);need(type(w['calls']) is int and w['calls']==8 and type(w['sink']) is int and w['bytes']==w['events']==w['compile_seconds']==w['recompile_seconds']==0,'zeroallocation wrapper')
   bp=[100*w[0]<97*v[0] for v,w in zip(a,b)];ep=[100*w[1]<97*v[1] for v,w in zip(a,b)];need(x['per_pair_bytes_predicate']==bp and x['per_pair_events_predicate']==ep and all(type(v) is bool for v in x['per_pair_bytes_predicate']+x['per_pair_events_predicate']),'unchanged strict3percent predicate')
   passed=all(bp) and all(ep);key=x['pattern'];location=[str(D/'generic_dual_comparisons_tests.jl'),lines['generic_dual_comparisons_tests.jl']]
  if not passed:locations.append(location)
  results.append(dict(kind=x['kind'],case=key,original_cost_gate_passed=passed,preparation_gc=x['gc_preparation'],before=a,after=b))
 fail=len(locations);need(exitcode==(1 if fail else 0),'ordinary Test exit agrees with actual gate results')
 header=next(v for v in log.splitlines() if v.startswith('Test Summary:') and '|' in v);line=next(v for v in log.splitlines() if v.startswith('Legacy allocation counter capture') and '|' in v);columns=line.split('|',1)[1].split()
 need(header.split('|',1)[1].split()==(['Pass','Fail','Total','Time'] if fail else ['Pass','Total','Time']),'exact ordinary summary')
 need([int(z) for z in columns[:-1]]==([23663-fail,fail,23663] if fail else [23663,23663]),'all23663original assertions executed')
 need([[path,int(n)] for path,n in re.findall(r'Test Failed at (.*?):(\d+)',log)]==locations,'only exact original cost gates failed')
 need(('COUNTER_CAPTURE_COMPLETE' in log)==(fail==0),'truthful final marker')
 for ch in changes:
  src=M/'test'/ch['file'];copy=D/ch['file'];need(sha(src)==ch['original_sha256'] and sha(copy)==ch['diagnostic_sha256'],'frozen source identity');need(copy.read_text().replace(ch['insertion'],'').replace(ch['preparation_insertion'],'')==src.read_text(),'exact unchanged test inverse')
 resources=[json.loads(v) for v in (D/'output/resources.jsonl').read_text().splitlines()];need(resources and all(v['available_kib']>=6*1024**2 and v['swap_used_kib']<=1024**2 for v in resources),'all resources');need(p['terminal_memory']['available_kib']>=6*1024**2 and p['terminal_memory']['swap_used_kib']<=1024**2,'terminalresources')
 unchanged();extra=[p[k][v] for k in ['runner','child'] for v in ['pgid','sid']];put('audit-host.json',host(extra));put('capture-data.json',records)
 put('audit.json',dict(accepted=True,scope='counter-data diagnosis only; not production qualification or replacement MASTER',original_MASTER_still_rejected=True,ordinary_test_passed=23663-fail,ordinary_test_failed=fail,ordinary_test_total=23663,named_cases=4,measured_records=24,source_unchanged=True,unchanged_thresholds=True,one_preregistered_postwarm_gc_trial=True,results=results,bindings={str(D/n):sha(D/n) for n in ['capture-data.json','output/run.log','output/process.json','pins.json','contract.json','source-inverse.json','audit.py','audit-host.json']}))
 print(json.dumps({k:v for k,v in read('audit.json').items() if k not in ['bindings','results']}))
if __name__=='__main__':main()
