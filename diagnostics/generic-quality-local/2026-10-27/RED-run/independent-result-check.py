from pathlib import Path
import json,hashlib,subprocess,os,datetime,re,math
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-local/2026-10-27');X=D/'RED-run';M=Path('/home/jspitz/JSimplex.jl')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(n):return json.loads((X/n).read_text())
pins=read('pins.json');admission=read('admission.json');audit=read('audit.json');proc=read('output/process.json');supervisor=read('supervisor.json');completed=read('completed.json');contract=read('contract.json')
assert audit['accepted'] is True and audit['passed']==16579 and audit['expected_failures']==4 and audit['total']==16583
for a in [admission,audit]:
 for n,v in a['bindings'].items():assert sha(n)==v,n
for n,v in pins['inventory'].items():assert str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'],n
for tree in pins['trees']:assert {str(p) for p in Path(tree).rglob('*') if p.is_file()}=={n for n in pins['inventory'] if Path(n).is_relative_to(tree)}
baseline=json.loads((D/'baseline-tree.json').read_text());assert len(baseline)==535
for n,h in baseline.items():
 assert sha(D/'baseline'/n)==h
 if n=='test/runtests.jl':assert (D/'RED'/n).read_bytes()==(D/'baseline'/n).read_bytes()+b'\ninclude("generic_quality_local_tests.jl")\n'
 else:assert sha(D/'RED'/n)==h,n
assert {str(p.relative_to(D/'RED')) for p in (D/'RED').rglob('*') if p.is_file()}==set(baseline)|{'test/generic_quality_local_tests.jl'}
testhash='12c0b1a8d0be69095f9588fa3057ee0d86b31bf0efbb0e8f11492898aaf139ce';assert sha(D/'new-test-draft.jl')==sha(D/'new-test.jl')==sha(D/'RED/test/generic_quality_local_tests.jl')==testhash
test=(D/'new-test.jl').read_text();assert test.count((D/'comparison-2/Reference.jl').read_text())==1
for arm in ['A','B','AB','C']:assert 'const LocalCandidate'+arm+'=JSimplex' in test
assert test.splitlines()[439].strip()=='@test all(new["bytes"]<old["bytes"]&&new["events"]<old["events"] for (old,new) in pairs) # RED whole-call cost gate'
assert test.count('for k in 1:3')==2 and 'if isodd(k);reset!(a);old=timed' in test
log=(X/'output/run.log').read_text();assert '0 errored, 0 broken' in log and 'Error During Test' not in log and 'Broken' not in log
head=next(s for s in log.splitlines() if s.startswith('Test Summary:'));assert head.split('|')[1].split()==['Pass','Fail','Total','Time']
root=next(s for s in log.splitlines() if s.startswith('Local quality RED') and '|' in s);assert root.split('|')[1].split()[:3]==['16579','4','16583']
locations=[[a,int(b)] for a,b in re.findall(r'Test Failed at (.*?):(\d+)',log)];assert locations==contract['expected_failure_locations'] and len(locations)==4
assert re.findall(r'^INCLUDING (.*)$',log,re.M)==contract['files']==['generic_quality_local_tests.jl']
assert 'LOCAL_QUALITY_SOURCE '+str(D/'RED/src/JSimplex.jl') in log and 'LOCAL_QUALITY_COMPLETED RED' not in log
blocks=re.findall(r'^Whole-call allocation (quality|quality_transposed|finish|audit): Test Failed at .*?\n  Expression: (.*?)\n   Evaluated: (.*?)\n',log,re.M)
assert [v[0] for v in blocks]==['quality','quality_transposed','finish','audit'];allocations=[]
for scope,expression,evaluated in blocks:
 assert expression=='all((new["bytes"] < old["bytes"] && new["events"] < old["events"] for (old, new) = pairs))'
 dicts=re.findall(r'Dict\(([^()]*)\)',evaluated);assert len(dicts)==6
 values=[]
 for entry in dicts:
  fields=dict(re.findall(r'"(\w+)" => ([0-9.eE+\-]+)',entry));assert set(fields)=={'gc_seconds','recompile_seconds','seconds','bytes','events','compile_seconds','sink'}
  v={k:float(val) for k,val in fields.items()};assert all(math.isfinite(vv) and vv>=0 for vv in v.values());assert v['compile_seconds']==v['recompile_seconds']==0;values.append(v)
 for i in range(0,6,2):assert values[i]['bytes']==values[i+1]['bytes'] and values[i]['events']==values[i+1]['events'] and values[i]['sink']==values[i+1]['sink']
 expected={'quality':(9524768,269652,4),'quality_transposed':(9524768,269652,4),'finish':(51040,1594,1),'audit':(983408,28526,1)}[scope]
 assert all((v['bytes'],v['events'],v['sink'])==expected for v in values);allocations.append(dict(scope=scope,bytes=expected[0],events=expected[1],sink=expected[2],pairs=3,all_pairs_equal=True))
assert proc['returncode']==contract['expected_exit']==1 and proc['reason']=='exit1' and proc['pins_unchanged'] is True and proc['command']==contract['command']
assert supervisor['accepted'] is True and supervisor['returncode']==0 and not supervisor['soft_timeout'] and not supervisor['hard_timeout'] and 'cleanup_error' not in supervisor
assert completed['accepted'] is True and completed['elapsed_shared_seconds']<=2400 and supervisor['elapsed_seconds']<=2400
cur=read('output/current.json');gate=read('output/gate.json');permit=read('output/permit.json');res=read('reservation.json')
assert gate['identity']==proc['child']==cur['child'] and gate['parent']==proc['runner']==cur['runner']==supervisor['guard_identity']
assert gate['command']==permit['command']==cur['command']==contract['command'] and gate['parent_death_signal']==9
assert gate['current_sha256']==permit['current_sha256']==sha(X/'output/current.json') and gate['permit_sha256']==sha(X/'output/permit.json')
assert sha(X/'output/pins.json')==sha(X/'pins.json')==proc['pins_sha256'] and res['guard_deadline']==res['started_monotonic']+2392 and res['outer_deadline']==res['started_monotonic']+2400
resources=[json.loads(l) for l in (X/'output/resources.jsonl').read_text().splitlines()];assert len(resources)==33 and all(v['available_kib']>=6*1024**2 and v['swap_used_kib']<=1024**2 for v in resources)
for n,v in {**read('protected-before.json')['files'],**read('protected-before.json')['indexes']}.items():assert sha(n)==v,n
refs=subprocess.check_output(['/usr/bin/git','-C',str(M),'rev-parse','HEAD','master','origin/master'],env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')).decode().splitlines();assert set(refs)=={'ca64312f7f74b1d7bec047718399f229674b3e1d'}
allowance=D/'host-identity-allowance.json';assert sha(allowance)=='f0b6a5093b9c1875ec8718bca8775bc44ba4d6d6ab98a1ac23adfe52d69f2a92';allow=json.loads(allowance.read_text());assert sha(allow['historical_record'])==allow['historical_sha256'] and json.loads(Path(allow['historical_record']).read_text())['child']==allow['historical_child'];assert len(allow['identities'])==1 and allow['identities'][0]['boot_id']!=allow['historical_child']['boot_id']
assert (X/'common.py').read_bytes()==(D/'common_next.py').read_bytes()
old=(D/'common.py').read_text();new=(D/'common_next.py').read_text();start=new.index('   if pgid in groups or sid in groups:');end=new.index('   need(not any(',start);replacement="   need(pgid not in groups and sid not in groups,'historical group/session');";assert new[:start]+replacement+new[end:].replace('   need(not any(','need(not any(',1)==old
h=read('host-seed.json');groups=set(h['groups'])|{proc[k][v] for k in ['runner','child'] for v in ['pgid','sid']};assert len(groups)==591;boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();assert boot==h['boot_id'];processes=[];collisions=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  st=(p/'stat').read_text().rsplit(')',1)[1].split();cmd=[v.decode(errors='replace') for v in (p/'cmdline').read_bytes().split(b'\0') if v];comm=(p/'comm').read_text().strip();actual=dict(pid=int(p.name),pgid=int(st[2]),sid=int(st[3]),start_ticks=int(st[19]),command=cmd,boot_id=boot)
  if actual['pgid'] in groups or actual['sid'] in groups:assert actual in allow['identities'];collisions.append(actual)
  assert not any(Path(v).name.lower().startswith('julia') for v in [comm]+cmd[:1]);processes.append(actual)
 except (FileNotFoundError,ProcessLookupError):pass
assert all(v in allow['identities'] for v in collisions) and len(collisions)<=1;mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};assert mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2
r=dict(accepted=True,findings=[],phase='RED expected whole-call cost failure',passed=16579,expected_allocation_failures=4,total=16583,unexpected_correctness_failures=0,errors=0,broken_or_skips=0,baseline_files_verified=535,inventory_files_verified=len(pins['inventory']),admission_bindings_verified=len(admission['bindings']),frozen_new_test_sha256=testhash,allocations=allocations,elapsed_shared_seconds=completed['elapsed_shared_seconds'],resource_samples=33,min_available_kib=min(v['available_kib'] for v in resources),max_swap_kib=max(v['swap_used_kib'] for v in resources),child_maxrss_kib=proc['child_maxrss_kib'],historical_groups_checked=591,sole_unrelated_collision=collisions,fresh_no_Julia=True,boot_id=boot,fresh_processes=processes,fresh_available_kib=mem['MemAvailable'],fresh_swap_used_kib=mem['SwapTotal']-mem['SwapFree'],checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),checker_sha256=sha(__file__))
with Path('/tmp/local-quality-RED-independent-result-evidence.json').open('x') as f:json.dump(r,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({k:v for k,v in r.items() if k not in ['fresh_processes','sole_unrelated_collision']}))
