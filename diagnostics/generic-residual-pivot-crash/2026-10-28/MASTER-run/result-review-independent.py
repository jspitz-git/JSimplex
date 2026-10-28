from pathlib import Path
import importlib.util,json,hashlib,subprocess,os,re,datetime
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-residual-pivot-crash/2026-10-28');P=D/'MASTER-run';M=Path('/home/jspitz/JSimplex.jl');G=D/'GREEN';TARGET='85f8275b85183f87fa8f33164cb0fbb5115f17ec';BASE='bb765d008c6e8aab6187aa0ea49d49a4f8a03309'
sp=importlib.util.spec_from_file_location('rpc_actual_master_result_common',P/'common.py');c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c)
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def git(a,env=None):return subprocess.check_output(['/usr/bin/git','-C',str(M),*a],env=env)
def put(n,v):
 with (P/n).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
c.unchanged();pins=read(P/'pins.json');assert len(pins['inventory'])==804
ad=read(P/'admission.json');assert ad['accepted'] is True and ad['findings']==[] and ad['expected_total']==ad['expected_passes']==362111 and ad['expected_failures']==0 and ad['expected_whole_files']==67 and len(ad['bindings'])==2533
for n,h in ad['bindings'].items():assert sha(n)==h,n
for n,h in read(P/'audit.json')['bindings'].items():assert sha(n)==h,n
con=read(P/'contract.json');gc=read(D/'GREEN-run/contract.json');gr=read(D/'GREEN-run/result-review.json');proc=read(P/'output/process.json');sup=read(P/'supervisor.json');done=read(P/'completed.json');inv=read(P/'invocation.json');res=read(P/'reservation.json');cur=read(P/'output/current.json');gate=read(P/'output/gate.json');permit=read(P/'output/permit.json')
assert con['files']==gc['files']==gr['required_MASTER_files'] and len(con['files'])==len(set(con['files']))==67
assert con['expected_total']==gr['total']==gr['required_MASTER_total']==362111 and con['expected_exit']==con['expected_failures']==0 and con['expected_failure_locations']==[]
assert proc['reason']=='exit0' and proc['returncode']==0 and proc['pins_unchanged'] is True
assert sup['accepted'] is True and sup['returncode']==0 and all(sup[k] is False for k in ['soft_timeout','hard_timeout','abnormal_cleanup_attempted','child_cleanup_attempted','child_kill','guard_term','guard_kill']) and 'cleanup_error' not in sup
assert done['accepted'] is True and done['pins_unchanged'] is True and done['limit_seconds']==3600 and 0<sup['elapsed_seconds']<=done['elapsed_shared_seconds']<=3600
assert proc['command']==inv['Julia_command']==con['command'] and proc['runner']['command']==' '.join(inv['command'])+' '
assert proc['pins_sha256']==res['pins_sha256']==sha(P/'pins.json')==sha(P/'output/pins.json') and res['admission_sha256']==sha(P/'admission.json')
assert res['attempt']==1 and res['started_monotonic']==inv['common_started'] and res['guard_deadline']==res['started_monotonic']+3592==inv['guard_deadline'] and res['outer_deadline']==res['started_monotonic']+3600==inv['outer_deadline']
assert proc['runner']==sup['guard_identity']==cur['runner']==gate['parent'] and proc['child']==cur['child']==gate['identity']
assert gate['command']==permit['command']==cur['command']==con['command'] and gate['parent_death_signal']==9
assert gate['current_sha256']==permit['current_sha256']==sha(P/'output/current.json') and gate['permit_sha256']==sha(P/'output/permit.json')
assert sha(P/'audit.py')==sha(D/'phase-audit.py')==ad['postexit_auditor_sha256'] and str(P/'audit.py') not in pins['inventory']
log=(P/'output/run.log').read_text();assert not re.search(r'Test Failed|Error During Test|^ERROR:|Test Broken',log,re.M)
assert re.findall(r'^INCLUDING (.*)$',log,re.M)==con['files'] and re.findall(r'^RPC_SOURCE (.*)$',log,re.M)==[str(M/'src/JSimplex.jl')]
headers=[x for x in log.splitlines() if x.startswith('Test Summary:')];assert len(headers)==1 and headers[0].split('|')[1].split()==['Pass','Total','Time']
roots=[x for x in log.splitlines() if x.startswith('Residual pivot crash MASTER') and '|' in x];assert len(roots)==1 and roots[0].split('|')[1].split()[:2]==['362111','362111'] and len(roots[0].split('|')[1].split())==3
assert log.count('RPC_COMPLETED MASTER')==1
resources=[json.loads(x) for x in (P/'output/resources.jsonl').read_text().splitlines()];assert len(resources)==2429
assert all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources)
assert all(a['elapsed']<=b['elapsed'] for a,b in zip(resources,resources[1:])) and max(x['elapsed'] for x in resources)<3592
assert proc['terminal_memory']['available_kib']>=6*1024**2 and proc['terminal_memory']['swap_used_kib']<=1024**2
co=read(D/'production-commit.json');cr=read(D/'commit-review.json');iv=read(D/'source-inverse.json');hist=read(D/'integration-historical-path-map.json');baseline=read(D/'baseline-tree.json');protected=read(D/'protected-before.json');before=read(D/'integration-before.json')
assert co['commit']==TARGET==ad['expected_commit'] and co['parent']==BASE==ad['expected_parent']
assert git(['rev-list','--parents','-n','1',TARGET]).decode().split()==[TARGET,BASE]
assert git(['rev-parse','HEAD']).decode().strip()==git(['rev-parse','master']).decode().strip()==TARGET and git(['branch','--show-current']).decode().strip()=='master'
assert git(['rev-parse','origin/master']).decode().strip()==BASE==git(['ls-remote','origin','refs/heads/master']).decode().split()[0]
assert c.git(['rev-parse','HEAD'],c.R)=='94394f8b91a4670c24f7fb9e7c23c468e4cadfd4'==c.git(['ls-remote','origin','refs/heads/codex/simplex-core-architecture'],c.R).split()[0]
raw=git(['ls-tree','-r','-z',TARGET]);assert hashlib.sha256(raw).hexdigest()==cr['full_tree_sha256']==read(P/'admission-evidence.json')['full_tree_sha256']
entries={}
for line in raw.split(b'\0'):
 if line:
  meta,name=line.split(b'\t',1);mode,kind,oid=meta.decode().split();entries[name.decode()]=(mode,kind,oid)
assert len(entries)==3560
assert {str(p.relative_to(G)) for p in G.rglob('*') if p.is_file()}==set(iv['whole_stage']) and len(iv['whole_stage'])==543
for n,h in iv['whole_stage'].items():
 assert sha(G/n)==sha(M/n)==h,n
 if n in entries:
  data=(M/n).read_bytes();assert entries[n]==('100644','blob',hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest())
for root in ['src','test']:
 assert {str(p.relative_to(M)) for p in (M/root).rglob('*') if p.is_file()}=={str(p.relative_to(G)) for p in (G/root).rglob('*') if p.is_file()}=={str(Path(n).relative_to(M)) for n in pins['inventory'] if Path(n).is_relative_to(M/root)}
mainindex=git(['rev-parse','--path-format=absolute','--git-path','index']).decode().strip();assert hist['master_before']==BASE and set(hist['master_index_before'])=={mainindex}
assert set(hist['source_before'])=={str(M/n) for n in co['names'] if n in baseline}
for actual,v in hist['source_before'].items():
 n=str(Path(actual).relative_to(M));assert v==dict(before=str(D/'baseline'/n),sha256=baseline[n]) and sha(v['before'])==v['sha256']
idx=hist['master_index_before'][mainindex];assert idx==dict(before=str(D/'before-master/master.index'),sha256=protected['indexes'][mainindex]) and sha(idx['before'])==idx['sha256']
assert git(['ls-files','--stage','-z'],env=dict(os.environ,GIT_INDEX_FILE=idx['before'],GIT_OPTIONAL_LOCKS='0')).decode().split('\0')==before['entries']
current=git(['ls-files','--stage','-z']).decode().split('\0')
def unrelated(xs):return [x for x in xs if x and x.split('\t',1)[1] not in co['names']]
assert unrelated(current)==unrelated(before['entries']) and git(['diff','--cached','--raw','-z']).decode()==before['staged']==''
for item in current:
 if item:
  meta,n=item.split('\t',1);mode,oid,stage=meta.split();assert stage=='0' and entries[n]==(mode,'blob',oid)
assert sha(idx['before'])==idx['sha256']
maps={**hist['source_before'],**hist['master_index_before']};resolved=set();cached={}
def digest(p):
 if p not in cached:cached[p]=sha(p)
 return cached[p]
for rel,count in [('pins.json',1251),('pins-ready.json',1268),('pins-final.json',1285),('output/pins.json',1285),('RED-run/pins.json',1328),('RED-run/output/pins.json',1328),('GREEN-run/pins.json',1329),('GREEN-run/output/pins.json',1329)]:
 manifest=read(D/rel);assert len(manifest['inventory'])==count
 for n,v in manifest['inventory'].items():
  assert str(Path(n).resolve(strict=True))==v['resolved']
  if digest(n)!=v['sha256']:
   assert n in maps and maps[n]['sha256']==v['sha256'] and digest(maps[n]['before'])==v['sha256'];resolved.add(n)
 for tree in manifest['trees']:
  root=Path(tree);want={n for n in manifest['inventory'] if Path(n).is_relative_to(root)}
  if root in [M/'src',M/'test']:actual={str(M/n) for n in baseline if Path(n).is_relative_to(root.relative_to(M))}
  else:actual={str(p) for p in root.rglob('*') if p.is_file()}
  assert actual==want
for n,h in protected['files'].items():assert sha(n)==h
for n,h in protected['indexes'].items():
 if sha(n)!=h:assert n==mainindex and sha(idx['before'])==h
assert len(resolved)==4
extra=[proc[k][v] for k in ['runner','child'] for v in ['pgid','sid']];host=c.host(extra);assert len(host['groups'])==667 and host['no_Julia'] is True and host['boot_id']=='781795f4-f7af-4c3b-9ce9-45c7cae76ecb'
# Read-only destination check; publication still uses the reviewed control and fresh checks.
allowed=['git@github.com:jspitz-git/JSimplex','https://github.com/jspitz-git/JSimplex','ssh://git@github.com/jspitz-git/JSimplex']
for args in [['remote','get-url','--push','--all','origin'],['remote','get-url','--all','origin']]:
 urls=[x.removesuffix('.git') for x in git(args).decode().splitlines()];assert len(urls)==1 and urls[0] in allowed
put('result-review-host.json',host)
e=dict(accepted=True,passed=362111,total=362111,expected_failures=0,whole_files=67,ordered_files=con['files'],current_pins=804,admission_bindings_verified=2533,complete_tested_stage_files=543,complete_commit_entries=3560,commit=TARGET,parent=BASE,tree=co['tree'],full_tree_sha256=hashlib.sha256(raw).hexdigest(),historical_existing_source_mappings_verified=4,raw_index_beforeimage_and_unrelated_entries_verified=True,historical_manifest_counts=[1251,1268,1285,1285,1328,1328,1329,1329],postexit_auditor_copy_verified=True,elapsed_shared_seconds=done['elapsed_shared_seconds'],samples=len(resources),minimum_available_kib=min(x['available_kib'] for x in resources),maximum_swap_kib=max(x['swap_used_kib'] for x in resources),child_maxrss_kib=proc['child_maxrss_kib'],no_timeout=True,no_Git_mutation=True,no_Julia_executed=True,no_auditor_rerun=True,host_time=host['time_utc'],historical_groups_and_sessions=667,remote_before_push=BASE)
put('result-review-evidence.json',e)
print(json.dumps({k:v for k,v in e.items() if k!='ordered_files'}))
