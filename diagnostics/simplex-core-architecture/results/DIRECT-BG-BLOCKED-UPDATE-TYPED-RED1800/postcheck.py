"""New saved-prefix and failure check. No Julia or admitted auditor execution."""
from pathlib import Path
import sys,json,tomllib,re
E=Path(__file__).resolve().parent;D=E.with_name('DIRECT-BG-BLOCKED-UPDATE-TYPED-RED1800-HARNESS');sys.path.insert(0,str(D));import control as c
from oracle import unit,metrics
run=D/'runs/red1800';o=D/'outers/red1800';out=run/'output';payload=run/'payload';checks={}
def ck(k,v):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
a=c.rd(run/'audit.json');p=c.rd(out/'process.json');inv=c.rd(run/'invocation.json');sup=inv['supervisor'];s=c.rd(run/'sealed.json');cl=c.rd(run/'outer-closure.json')
ck('failed_admitted_audit_preserved',a['all_passed'] is False and a['pure_timeout'] is False and a['error']=="RuntimeError('Exact payload membership')" and c.bindings(a))
c.verify_review(c.rd(run/'admission.json'),run/'sealed.json',s['files']+[str(run/'sealed.json')],'BG blocked typed RED repeat exact-run admission','red1800');ck('admission_exact_bindings',True)
c.verify_seal(c.config('red1800'),s);ck('sealed_inventory_unchanged',True)
ck('launch_inventory_unchanged',c.guard.pins_match(c.rd(run/'launch-pins.json')) and c.rd(out/'pins.json')==c.rd(run/'launch-pins.json') and p['pins_unchanged'] is True)
ck('segfault_not_expected_RED_exit',p['returncode']==-11 and p['reason']=='exit-11' and sup['returncode']==1 and sup['accepted'] is False and c.rd(o/'outer-outcome.json')['returncode']==2)
ck('no_timeout_or_termination',all(sup[k] is False for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']))
ck('elapsed_below_limits',0<=p['elapsed_including_launch']<=1792 and 0<=inv['elapsed_seconds']<=1800 and 0<=sup['elapsed_seconds']<=1800)
ck('external_closure',c.validate_result_closure('red1800',cl))
h=cl['host'];ck('full292groups_sessions_closed',len(h['groups'])==292 and c.host_safe(h))
expected={f'unit-{i}.toml' for i in range(1,13)}|{f'cost-{i}.toml' for i in range(1,13)}|{'load.toml','panel-load.toml','tests-load.toml'}
ck('exact27_payload_prefix',{f.name for f in payload.iterdir()}==expected and all(f.is_file() and not f.is_symlink() for f in payload.iterdir()))
data={f.name:tomllib.loads(f.read_text()) for f in payload.iterdir()};schedule=c.rd(D/'schedule.json');totals=[0]*4;failures=[];rows=[]
for i in range(1,13):
 u=data[f'unit-{i}.toml'];t=unit(u,i,schedule,'red');totals=[x+y for x,y in zip(totals,t)];failures.extend(dict(unit=u['name'],**f) for f in u['records']['failures']);rows.append(dict(index=i,name=u['name'],totals=t))
ck('source_bound_saved_prefix',True)
ck('only_two_expectedN026',len(failures)==2 and {f['unit'] for f in failures}=={'dense96/native','dense96/markowitz'} and all(f['site']=='N026' and f['kind']=='fail' for f in failures) and totals[1:]==[2,0,0])
ck('panel_P011_zero_and_preservation_PASS',rows[0]['totals']==[11768,0,0,0] and data['unit-1.toml']['records']['sites']['P011']==1 and all(data['unit-1.toml']['records']['sites'][f'P{i:03d}']==1 for i in range(95,103)))
costs={n:metrics(v) for n,v in data.items() if not n.startswith('unit-')};ck('15_saved_costs',len(costs)==15)
log=(out/'run.log').read_text();ck('interrupted_dense256_native',log.count('UNIT BEGIN 13 dense256/native\n')==1 and 'UNIT END 13' not in log and 'UNIT BEGIN 14' not in log)
ck('OOM_before_finalizer_SIGSEGV','OutOfMemoryError()' in log and 'signal 11' in log and log.index('OutOfMemoryError()')<log.index('signal 11') and 'run_finalizer' in log)
ck('no_full_raw_or_acceptedRED',not (payload/'raw.toml').exists() and not (run/'result-review.json').exists())
resources=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()]
ck('availableRAM_swap_guards_held',bool(resources) and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources+[p['terminal_memory']]))
mem={k:[] for k in ['VmPeak','VmHWM','VmRSS','VmSwap']}
for sample in resources:
 for line in sample.get('child_memory',[]):
  m=re.fullmatch(r'(VmPeak|VmHWM|VmRSS|VmSwap):\s+(\d+) kB',line)
  if m:mem[m[1]].append(int(m[2]))
ck('sampled_VM_peak_reached8GiB',max(mem['VmPeak'])==8*1024**2)
ck('source_RLIMIT_AS8GiB','resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))' in (D/'guard.py').read_text())
c.validate_timeout_record();ck('old_timeout_evidence_unchanged',True)
files=sorted([f for root in [run,o] for f in root.rglob('*') if f.is_file()]+[E/n for n in ['postcheck.py','host-entry.json','entry-check.json','request.txt','outer.log']])
result=dict(all_passed=True,qualification_accepted=False,pure_timeout_qualification_proven=False,checks=checks,completed_units=rows,saved_prefix_totals=totals,failures=failures,preparation=costs,group_count=len(h['groups']),identities=dict(outer=s['outer_identity'],runner=p['runner'],child=p['child']),process_seconds=p['elapsed_including_launch'],supervisor_seconds=sup['elapsed_seconds'],outer_seconds=c.rd(o/'outer-outcome.json')['elapsed_with_checks_seconds'],resource_summary=dict(samples=len(resources),min_available_kib=min(x['available_kib'] for x in resources),max_swap_used_kib=max(x['swap_used_kib'] for x in resources),terminal=p['terminal_memory'],child_maxrss_kib=p['child_maxrss_kib'],sampled_max_kib={k:max(v) for k,v in mem.items()}),sha256={str(f):c.sha(f) for f in files},scope='Faithful OOM/SIGSEGV diagnostic and completed prefix only. Exact first failing allocation is unknown; full RED rejected. No auditor or numerical rerun.')
c.save(E/'postcheck.json',result)
print(json.dumps({k:result[k] for k in ['all_passed','qualification_accepted','saved_prefix_totals','group_count','resource_summary','process_seconds','supervisor_seconds']}))
