from pathlib import Path
import json,hashlib,subprocess,os,datetime,re,math
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-local/2026-10-27');X=D/'MASTER-run';M=Path('/home/jspitz/JSimplex.jl');S=D/'GREEN'
TARGET='1a6b9d81e89b44c5c75b95b6c92e0916c2d19730';BASE='ca64312f7f74b1d7bec047718399f229674b3e1d'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(n):return json.loads((X/n).read_text())
def git(*args,input=None,extra_env=None):return subprocess.check_output(['/usr/bin/git','-C',str(M),*args],input=input,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',**(extra_env or {})))
def grev(*args):return git(*args).decode().strip()
pins=read('pins.json');admission=read('admission.json');audit=read('audit.json');proc=read('output/process.json');supervisor=read('supervisor.json');completed=read('completed.json');contract=read('contract.json')
assert contract['arm']=='MASTER' and contract['source_root']==str(M) and contract['expected_total']==203205 and contract['expected_exit']==0
assert audit['accepted'] is True and audit['expected_failures']==0 and audit['passed']==audit['total']==203205
for a in [admission,audit]:
 for n,v in a['bindings'].items():assert sha(n)==v,n
for n,v in pins['inventory'].items():assert str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'],n
for tree in pins['trees']:assert {str(p) for p in Path(tree).rglob('*') if p.is_file()}=={n for n in pins['inventory'] if Path(n).is_relative_to(tree)}
assert len(pins['inventory'])==697
commit=json.loads((D/'production-commit.json').read_text());review=json.loads((D/'commit-review.json').read_text());inverse=json.loads((D/'source-inverse.json').read_text());green_audit=json.loads((D/'GREEN-run/audit.json').read_text());green_review=json.loads((D/'GREEN-run/result-review.json').read_text())
assert review['accepted'] is True and review['findings']==[] and green_review['accepted'] is True and green_review['findings']==[] and green_audit['accepted'] is True and green_audit['total']==203205
for n,h in review['bindings'].items():assert sha(n)==h,n
assert commit['commit']==review['commit']==TARGET and commit['parent']==review['parent']==BASE and commit['names']==review['names']==inverse['names']
assert grev('rev-parse','HEAD')==grev('rev-parse','master')==TARGET and grev('rev-parse','origin/master')==BASE
assert grev('rev-list','--parents','-n','1',TARGET).split()==[TARGET,BASE] and grev('rev-parse',TARGET+'^{tree}')==commit['tree']==review['tree']
assert grev('diff-tree','--no-commit-id','--name-only','-r',BASE,TARGET).splitlines()==commit['names']==['src/primal_updates.jl','src/simplex_numerics.jl','test/generic_quality_local_tests.jl','test/runtests.jl']
actual={str(p.relative_to(M)):sha(p) for t in ['src','test'] for p in (M/t).rglob('*') if p.is_file()};stage={str(p.relative_to(S)):sha(p) for t in ['src','test'] for p in (S/t).rglob('*') if p.is_file()};assert len(actual)==533 and actual==stage==review['actual_commit_sha256']
entries=[]
for rec in git('ls-tree','-r','-z',TARGET,'--','src','test').split(b'\0'):
 if not rec:continue
 meta,path=rec.split(b'\t',1);mode,kind,blob=meta.split();assert kind==b'blob';entries.append((path.decode(),blob.decode()))
assert {n for n,h in entries}==set(actual)
raw=git('cat-file','--batch',input=''.join(h+'\n' for n,h in entries).encode());offset=0;committed={};gitblobs={}
for name,blob in entries:
 stop=raw.index(b'\n',offset);got,kind,length=raw[offset:stop].split();assert got.decode()==blob and kind==b'blob';size=int(length);data=raw[stop+1:stop+1+size];assert raw[stop+1+size:stop+2+size]==b'\n';offset=stop+2+size
 assert hashlib.sha1(b'blob '+str(size).encode()+b'\0'+data).hexdigest()==blob
 committed[name]=hashlib.sha256(data).hexdigest();gitblobs[name]=blob;assert data==(M/name).read_bytes()==(S/name).read_bytes(),name
assert offset==len(raw) and committed==actual
for n,h in commit['blobs'].items():assert gitblobs[n]==h
changes=json.loads((D/'changes.json').read_text());baseline=json.loads((D/'baseline-tree.json').read_text());assert len(baseline)==535 and {str(p.relative_to(D/'baseline')) for p in (D/'baseline').rglob('*') if p.is_file()}==set(baseline)
for n,h in baseline.items():assert sha(D/'baseline'/n)==h,n
for file in ['simplex_numerics.jl','primal_updates.jl']:
 original=(D/'baseline/src'/file).read_text();forward=original
 for k in ['A','B','C']:
  v=changes[k]
  if v['file']==file:assert forward.count(v['old'])==1;forward=forward.replace(v['old'],v['new'])
 current=(M/'src'/file).read_text();assert current==forward
 for k in ['C','B','A']:
  v=changes[k]
  if v['file']==file:assert current.count(v['new'])==1;current=current.replace(v['new'],v['old'])
 assert current==original
for n,h in inverse['whole_stage'].items():assert sha(S/n)==h,n
assert {str(p.relative_to(S)) for p in S.rglob('*') if p.is_file()}==set(inverse['whole_stage'])
hist=json.loads((D/'integration-historical-path-map.json').read_text());before=json.loads((D/'integration-before.json').read_text());after=json.loads((D/'integration-after.json').read_text())
assert hist['master_before']==BASE and hist['older_maps_preserved'] is True and before['target']==after['target']==TARGET and after['fast_forward'] is True and after['pushed'] is False and after['unrelated_indexes_unchanged'] is True
assert set(hist['source_before'])=={str(M/n) for n in commit['names'] if (D/'baseline'/n).exists()}
for n,v in hist['source_before'].items():assert sha(v['before'])==v['sha256']==baseline[str(Path(n).relative_to(M))]
for index,v in hist['master_index_before'].items():
 assert sha(v['before'])==v['sha256']=='10b5f71e4b0dc43e2bbdcfe625e8ee4c6e4c62a676ff786a373667c648ff911e'
 old_entries=git('ls-files','--stage','-z',extra_env={'GIT_INDEX_FILE':v['before']}).decode().split('\0');assert old_entries==before['entries']
current_entries=git('ls-files','--stage','-z').decode().split('\0');unrelated=lambda a:[s for s in a if s and s.split('\t',1)[1] not in commit['names']]
assert unrelated(current_entries)==unrelated(before['entries']) and git('diff','--cached','--raw','-z').decode()==before['staged']
assert not grev('diff','--name-only','HEAD','--','src','test','Project.toml')
for n,v in {**read('protected-before.json')['files'],**read('protected-before.json')['indexes']}.items():assert sha(n)==v,n
master_index=grev('rev-parse','--path-format=absolute','--git-path','index');assert sha(master_index)=='f7ddf5ce55d30de0d2eda7231cae7fce23885f1b926086644afb384dedaef34f'
testhash='12c0b1a8d0be69095f9588fa3057ee0d86b31bf0efbb0e8f11492898aaf139ce';assert sha(M/'test/generic_quality_local_tests.jl')==sha(D/'new-test.jl')==sha(D/'new-test-draft.jl')==testhash
assert contract['files']==json.loads((D/'GREEN-run/contract.json').read_text())['files'] and len(contract['files'])==35
log=(X/'output/run.log').read_text();assert 'Test Failed at ' not in log and 'Error During Test' not in log and not re.search(r'^ERROR:',log,re.M)
head=next(s for s in log.splitlines() if s.startswith('Test Summary:'));assert head.split('|')[1].split()==['Pass','Total','Time']
root=next(s for s in log.splitlines() if s.startswith('Local quality MASTER') and '|' in s);cols=root.split('|')[1].split();assert len(cols)==3 and int(cols[0])==int(cols[1])==203205
assert re.findall(r'^INCLUDING (.*)$',log,re.M)==contract['files'] and 'LOCAL_QUALITY_SOURCE '+str(M/'src/JSimplex.jl') in log and log.count('LOCAL_QUALITY_COMPLETED MASTER')==1
# Root-only ordinary success output: unchanged included source + exact count proves four gates.
test=(M/'test/generic_quality_local_tests.jl').read_text();assert test.splitlines()[439].strip()=='@test all(new["bytes"]<old["bytes"]&&new["events"]<old["events"] for (old,new) in pairs) # RED whole-call cost gate'
assert 'for (scope,pattern,m,arm) in ((:quality,:negative,0,:AB),(:quality_transposed,:negative,0,:AB),(:finish,:mixed,0,:B),(:audit,:positive,4,:C))' in test
assert proc['returncode']==0 and proc['reason']=='exit0' and proc['pins_unchanged'] is True and proc['command']==contract['command']
assert supervisor['accepted'] is True and supervisor['returncode']==0 and not supervisor['soft_timeout'] and not supervisor['hard_timeout'] and 'cleanup_error' not in supervisor
assert completed['accepted'] is True and completed['elapsed_shared_seconds']<=2400 and supervisor['elapsed_seconds']<=2400
cur=read('output/current.json');gate=read('output/gate.json');permit=read('output/permit.json');res=read('reservation.json')
assert gate['identity']==proc['child']==cur['child'] and gate['parent']==proc['runner']==cur['runner']==supervisor['guard_identity']
assert gate['command']==permit['command']==cur['command']==contract['command'] and gate['parent_death_signal']==9
assert gate['current_sha256']==permit['current_sha256']==sha(X/'output/current.json') and gate['permit_sha256']==sha(X/'output/permit.json')
assert sha(X/'output/pins.json')==sha(X/'pins.json')==proc['pins_sha256'] and res['guard_deadline']==res['started_monotonic']+2392 and res['outer_deadline']==res['started_monotonic']+2400
resources=[json.loads(l) for l in (X/'output/resources.jsonl').read_text().splitlines()];assert len(resources)==audit['samples'] and resources and all(v['available_kib']>=6*1024**2 and v['swap_used_kib']<=1024**2 for v in resources)
assert proc['terminal_memory']['available_kib']>=6*1024**2 and proc['terminal_memory']['swap_used_kib']<=1024**2
for name in ['launch.py','audit.py']:assert (X/name).read_bytes()==(D/'GREEN-run'/name).read_bytes(),name
for name in ['entry_gate.py','guard_reviewed.py','supervisor_reviewed.py']:assert (X/'guard'/name).read_bytes()==(D/'GREEN-run/guard'/name).read_bytes()
green_common=(D/'GREEN-run/common.py').read_text();actual_common=(X/'common.py').read_text();expected_common=green_common.replace("TARGET='"+BASE+"'","TARGET='"+TARGET+"'").replace("git(['rev-parse','HEAD'])==git(['rev-parse','master'])==git(['rev-parse','origin/master'])==TARGET","git(['rev-parse','HEAD'])==git(['rev-parse','master'])==TARGET and git(['rev-parse','origin/master'])=='"+BASE+"'");assert actual_common==expected_common
allowance=D/'host-identity-allowance.json';assert sha(allowance)=='f0b6a5093b9c1875ec8718bca8775bc44ba4d6d6ab98a1ac23adfe52d69f2a92';allow=json.loads(allowance.read_text());assert sha(allow['historical_record'])==allow['historical_sha256'] and json.loads(Path(allow['historical_record']).read_text())['child']==allow['historical_child'];assert len(allow['identities'])==1 and allow['identities'][0]['boot_id']!=allow['historical_child']['boot_id']
h=read('host-seed.json');groups=set(h['groups'])|{proc[k][v] for k in ['runner','child'] for v in ['pgid','sid']};assert len(groups)==595;boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();assert boot==h['boot_id'];processes=[];collisions=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  st=(p/'stat').read_text().rsplit(')',1)[1].split();cmd=[v.decode(errors='replace') for v in (p/'cmdline').read_bytes().split(b'\0') if v];comm=(p/'comm').read_text().strip();actual_identity=dict(pid=int(p.name),pgid=int(st[2]),sid=int(st[3]),start_ticks=int(st[19]),command=cmd,boot_id=boot)
  if actual_identity['pgid'] in groups or actual_identity['sid'] in groups:assert actual_identity in allow['identities'];collisions.append(actual_identity)
  assert not any(Path(v).name.lower().startswith('julia') for v in [comm]+cmd[:1]);processes.append(actual_identity)
 except (FileNotFoundError,ProcessLookupError):pass
assert all(v in allow['identities'] for v in collisions) and len(collisions)<=1;mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};assert mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2
r=dict(accepted=True,findings=[],phase='actual MASTER at reviewed commit',commit=TARGET,parent=BASE,origin_master_before_push=BASE,passed=203205,total=203205,failures=0,errors=0,broken_or_skips=0,ordered_files=contract['files'],committed_actual_stage_source_test_files=533,all_committed_blobs_rehashed=True,baseline_beforeimage_files_verified=535,exact_source_forward_inverse=True,exact_changed_names=commit['names'],current_index_uses_updated_snapshot=True,original_index_and_source_beforeimages_preserved=True,unrelated_index_entries_and_staged_changes_preserved=True,inventory_files_verified=len(pins['inventory']),admission_bindings_verified=len(admission['bindings']),frozen_new_test_sha256=testhash,four_frozen_allocation_gates_passed=True,elapsed_shared_seconds=completed['elapsed_shared_seconds'],resource_samples=len(resources),min_available_kib=min(v['available_kib'] for v in resources),max_swap_kib=max(v['swap_used_kib'] for v in resources),child_maxrss_kib=proc['child_maxrss_kib'],historical_groups_checked=595,sole_unrelated_collision=collisions,fresh_no_Julia=True,boot_id=boot,fresh_processes=processes,fresh_available_kib=mem['MemAvailable'],fresh_swap_used_kib=mem['SwapTotal']-mem['SwapFree'],checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),checker_sha256=sha(__file__))
with Path('/tmp/local-quality-MASTER-independent-result-evidence-v1.json').open('x') as f:json.dump(r,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({k:v for k,v in r.items() if k not in ['fresh_processes','sole_unrelated_collision','ordered_files']}))
