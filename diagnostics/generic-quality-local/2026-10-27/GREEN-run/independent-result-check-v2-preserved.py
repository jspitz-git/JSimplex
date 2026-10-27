from pathlib import Path
import json,hashlib,subprocess,os,datetime,re,math
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-local/2026-10-27');X=D/'GREEN-run';M=Path('/home/jspitz/JSimplex.jl');S=D/'GREEN'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(n):return json.loads((X/n).read_text())
pins=read('pins.json');admission=read('admission.json');audit=read('audit.json');proc=read('output/process.json');supervisor=read('supervisor.json');completed=read('completed.json');contract=read('contract.json')
assert audit['accepted'] is True and audit['expected_failures']==0 and audit['passed']==audit['total']>=1000
prior_audit_path=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-devex/2026-10-27/MASTER-run/audit.json');prior_audit=json.loads(prior_audit_path.read_text());red_result=json.loads((D/'RED-run/result-review.json').read_text());assert prior_audit['accepted'] is True and prior_audit['total']==186622 and red_result['total']==16583 and audit['total']==prior_audit['total']+red_result['total']==203205
for a in [admission,audit]:
 for n,v in a['bindings'].items():assert sha(n)==v,n
for n,v in pins['inventory'].items():assert str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'],n
for tree in pins['trees']:assert {str(p) for p in Path(tree).rglob('*') if p.is_file()}=={n for n in pins['inventory'] if Path(n).is_relative_to(tree)}
for prev in [D/'RED-run/result-review.json',D/'comparison-2/result-review.json']:
 a=json.loads(prev.read_text());assert a['accepted'] is True and a['findings']==[]
 for n,v in a['bindings'].items():assert sha(n)==v,n
baseline=json.loads((D/'baseline-tree.json').read_text());inverse=json.loads((D/'source-inverse.json').read_text());changes=json.loads((D/'changes.json').read_text());stage={str(p.relative_to(S)):sha(p) for p in S.rglob('*') if p.is_file()};assert len(baseline)==535 and len(stage)==536 and stage==inverse['whole_stage']
names=sorted(n for n,v in stage.items() if n not in baseline or baseline[n]!=v);assert names==inverse['names']==['src/primal_updates.jl','src/simplex_numerics.jl','test/generic_quality_local_tests.jl','test/runtests.jl']
for file in ['simplex_numerics.jl','primal_updates.jl']:
 original=(D/'baseline/src'/file).read_text();forward=original
 for key in ['A','B','C']:
  v=changes[key]
  if v['file']==file:assert forward.count(v['old'])==1;forward=forward.replace(v['old'],v['new'])
 current=(S/'src'/file).read_text();assert forward==current
 for key in ['C','B','A']:
  v=changes[key]
  if v['file']==file:assert current.count(v['new'])==1;current=current.replace(v['new'],v['old'])
 assert current==original
for n,h in baseline.items():
 assert sha(D/'baseline'/n)==h
 if n not in ['src/primal_updates.jl','src/simplex_numerics.jl','test/runtests.jl']:assert stage[n]==h,n
assert (S/'test/runtests.jl').read_bytes()==(D/'baseline/test/runtests.jl').read_bytes()+b'\ninclude("generic_quality_local_tests.jl")\n'
testhash='12c0b1a8d0be69095f9588fa3057ee0d86b31bf0efbb0e8f11492898aaf139ce';assert sha(D/'new-test-draft.jl')==sha(D/'new-test.jl')==sha(D/'RED/test/generic_quality_local_tests.jl')==sha(S/'test/generic_quality_local_tests.jl')==testhash
prior=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-devex/2026-10-27/GREEN-run/contract.json');oldfiles=json.loads(prior.read_text())['files'];assert len(oldfiles)==34 and len(contract['files'])==35 and contract['files']==['generic_quality_local_tests.jl']+oldfiles
log=(X/'output/run.log').read_text();assert 'Test Failed at ' not in log and 'Error During Test' not in log and not re.search(r'^ERROR:',log,re.M)
head=next(s for s in log.splitlines() if s.startswith('Test Summary:'));assert head.split('|')[1].split()==['Pass','Total','Time']
root=next(s for s in log.splitlines() if s.startswith('Local quality GREEN') and '|' in s);cols=root.split('|')[1].split();assert len(cols)==3 and int(cols[0])==int(cols[1])==audit['passed']
assert re.findall(r'^INCLUDING (.*)$',log,re.M)==contract['files'] and 'LOCAL_QUALITY_SOURCE '+str(S/'src/JSimplex.jl') in log and log.count('LOCAL_QUALITY_COMPLETED GREEN')==1
for scope in ['quality','quality_transposed','finish','audit']:
 line=next(s for s in log.splitlines() if re.match(r'\s+Whole-call allocation '+scope+r'\s+\|',s));assert line.split('|')[1].split()[:2]==['4','4']
clarification=json.loads((D/'production-review-count-clarification.json').read_text());assert clarification['accepted'] is True and clarification['findings']==[]
for n,v in clarification['bindings'].items():assert sha(n)==v
summary=json.loads((D/'comparison-2/summary.json').read_text());r=next(r for r in summary['cases'] if r['context']=='BF128_RoundingMode{:Nearest}()' and r['n']==96 and (r['variant'],r['scope'],r['density'],r['pattern'])==('A','quality','dense','mixed'));assert r['original']['bytes']==8190752 and r['candidate']['bytes']==7527200
assert proc['returncode']==contract['expected_exit']==0 and proc['reason']=='exit0' and proc['pins_unchanged'] is True and proc['command']==contract['command']
assert supervisor['accepted'] is True and supervisor['returncode']==0 and not supervisor['soft_timeout'] and not supervisor['hard_timeout'] and 'cleanup_error' not in supervisor
assert completed['accepted'] is True and completed['elapsed_shared_seconds']<=2400 and supervisor['elapsed_seconds']<=2400
cur=read('output/current.json');gate=read('output/gate.json');permit=read('output/permit.json');res=read('reservation.json')
assert gate['identity']==proc['child']==cur['child'] and gate['parent']==proc['runner']==cur['runner']==supervisor['guard_identity']
assert gate['command']==permit['command']==cur['command']==contract['command'] and gate['parent_death_signal']==9
assert gate['current_sha256']==permit['current_sha256']==sha(X/'output/current.json') and gate['permit_sha256']==sha(X/'output/permit.json')
assert sha(X/'output/pins.json')==sha(X/'pins.json')==proc['pins_sha256'] and res['guard_deadline']==res['started_monotonic']+2392 and res['outer_deadline']==res['started_monotonic']+2400
resources=[json.loads(l) for l in (X/'output/resources.jsonl').read_text().splitlines()];assert len(resources)==audit['samples'] and resources and all(v['available_kib']>=6*1024**2 and v['swap_used_kib']<=1024**2 for v in resources)
for n,v in {**read('protected-before.json')['files'],**read('protected-before.json')['indexes']}.items():assert sha(n)==v,n
refs=subprocess.check_output(['/usr/bin/git','-C',str(M),'rev-parse','HEAD','master','origin/master'],env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')).decode().splitlines();assert set(refs)=={'ca64312f7f74b1d7bec047718399f229674b3e1d'}
allowance=D/'host-identity-allowance.json';assert sha(allowance)=='f0b6a5093b9c1875ec8718bca8775bc44ba4d6d6ab98a1ac23adfe52d69f2a92';allow=json.loads(allowance.read_text());assert sha(allow['historical_record'])==allow['historical_sha256'] and json.loads(Path(allow['historical_record']).read_text())['child']==allow['historical_child'];assert len(allow['identities'])==1 and allow['identities'][0]['boot_id']!=allow['historical_child']['boot_id']
for name in ['common.py','launch.py','audit.py']:assert (X/name).read_bytes()==(D/'RED-run'/name).read_bytes(),name
for name in ['entry_gate.py','guard_reviewed.py','supervisor_reviewed.py']:assert (X/'guard'/name).read_bytes()==(D/'RED-run/guard'/name).read_bytes()
h=read('host-seed.json');groups=set(h['groups'])|{proc[k][v] for k in ['runner','child'] for v in ['pgid','sid']};assert len(groups)==593;boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();assert boot==h['boot_id'];processes=[];collisions=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  st=(p/'stat').read_text().rsplit(')',1)[1].split();cmd=[v.decode(errors='replace') for v in (p/'cmdline').read_bytes().split(b'\0') if v];comm=(p/'comm').read_text().strip();actual=dict(pid=int(p.name),pgid=int(st[2]),sid=int(st[3]),start_ticks=int(st[19]),command=cmd,boot_id=boot)
  if actual['pgid'] in groups or actual['sid'] in groups:assert actual in allow['identities'];collisions.append(actual)
  assert not any(Path(v).name.lower().startswith('julia') for v in [comm]+cmd[:1]);processes.append(actual)
 except (FileNotFoundError,ProcessLookupError):pass
assert all(v in allow['identities'] for v in collisions) and len(collisions)<=1;mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};assert mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2
r=dict(accepted=True,findings=[],phase='GREEN exact staged source and 35 complete files',passed=audit['passed'],total=audit['total'],failures=0,errors=0,broken_or_skips=0,ordered_files=contract['files'],baseline_files_verified=535,stage_files_verified=536,changed_names=names,exact_source_forward_inverse=True,inventory_files_verified=len(pins['inventory']),admission_bindings_verified=len(admission['bindings']),frozen_new_test_sha256=testhash,four_frozen_allocation_gates_passed=True,logical_count_sum=dict(prior34=186622,new_file=16583,whole35=203205,prior_audit_path=str(prior_audit_path),prior_audit_sha256=sha(prior_audit_path)),production_count_clarification_accepted=True,exact_A_dense_mixed_bytes=[8190752,7527200],elapsed_shared_seconds=completed['elapsed_shared_seconds'],resource_samples=len(resources),min_available_kib=min(v['available_kib'] for v in resources),max_swap_kib=max(v['swap_used_kib'] for v in resources),child_maxrss_kib=proc['child_maxrss_kib'],historical_groups_checked=593,sole_unrelated_collision=collisions,fresh_no_Julia=True,boot_id=boot,fresh_processes=processes,fresh_available_kib=mem['MemAvailable'],fresh_swap_used_kib=mem['SwapTotal']-mem['SwapFree'],checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),checker_sha256=sha(__file__))
with Path('/tmp/local-quality-GREEN-independent-result-evidence.json').open('x') as f:json.dump(r,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({k:v for k,v in r.items() if k not in ['fresh_processes','sole_unrelated_collision','ordered_files']}))
