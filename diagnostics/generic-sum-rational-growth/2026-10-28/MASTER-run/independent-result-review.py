from pathlib import Path
import json,hashlib,os,subprocess,datetime,re,math
P=Path(__file__).resolve().parent;D=P.parent;M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2]
TARGET='bb765d008c6e8aab6187aa0ea49d49a4f8a03309';BASE='ce5d4a74019e0dc2e656d08161641c498b159e7b'
def need(x,m):
 if not x:raise RuntimeError(m)
def read(p):return json.loads(Path(p).read_text())
cache={}
def sha(p):
 p=str(p)
 if p not in cache:
  with Path(p).open('rb') as f:cache[p]=hashlib.file_digest(f,'sha256').hexdigest()
 return cache[p]
def put(n,v):
 with (P/n).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
pins=read(P/'pins.json');need(len(pins['inventory'])==838,'current pins')
for n,v in pins['inventory'].items():need(str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'],'current pin '+n)
for tree in pins['trees']:need({str(p) for p in Path(tree).rglob('*') if p.is_file()}=={n for n in pins['inventory'] if Path(n).is_relative_to(tree)},'current tree membership')
mapdata=read(D/'integration-historical-path-map.json');need(mapdata['master_before']==BASE and mapdata['older_maps_preserved'] is True,'historical map base')
mapping={**mapdata['source_before'],**mapdata['master_index_before']}
need(set(mapdata['source_before'])=={str(M/n) for n in ['src/dual_simplex.jl','src/factorization.jl','test/runtests.jl']} and set(mapdata['master_index_before'])=={str(M/'.git/index')},'exact historical path domain')
for n,v in mapping.items():need(sha(v['before'])==v['sha256'],'historical before bytes '+n)
def historical_hash(n,h):
 if sha(n)==h:return
 need(n in mapping and mapping[n]['sha256']==h and sha(mapping[n]['before'])==h,'unexplained historical drift '+n)
for name in ['commit-review.json','production-review.json','GREEN-run/result-review.json','RED-run/result-review.json','result-review.json']:
 review=read(D/name);need(review['accepted'] is True and review['findings']==[],'accepted prior review '+name)
 for n,h in review['bindings'].items():historical_hash(n,h)
# Old inventories retain their actual before hashes; never rewrite or rerun old checks.
historical_counts={}
for name in ['pins.json','pins-reviewed.json','pins-ready.json','correctness-qualification/pins.json','RED-run/pins.json','GREEN-run/pins.json']:
 old=read(D/name);historical_counts[name]=len(old['inventory'])
 for n,v in old['inventory'].items():need(str(Path(n).resolve(strict=True))==v['resolved'],'historical resolution '+n);historical_hash(n,v['sha256'])
 for tree in old['trees']:
  actual={str(p) for p in Path(tree).rglob('*') if p.is_file()};expected={n for n in old['inventory'] if Path(n).is_relative_to(tree)}
  if Path(tree)==M/'test':actual.discard(str(M/'test/generic_sum_rational_growth_tests.jl'))
  need(actual==expected,'historical membership with explicit new test '+tree)
protected=read(P/'protected-before.json');originalprotected=read(D/'protected-before.json')
for section in protected.values():
 for n,h in section.items():need(sha(n)==h,'current protected '+n)
need(protected['files']==originalprotected['files'],'user-file hash baseline unchanged')
for n,h in originalprotected['indexes'].items():historical_hash(n,h)
for n,h in protected['indexes'].items():
 if n!=str(M/'.git/index'):need(h==originalprotected['indexes'][n],'unrelated index unchanged')
source=read(D/'source-inverse.json');need(source['accepted'] is True and source['production_baseline']==BASE,'accepted source inventory')
for n,h in source['whole_stage'].items():need(sha(M/n)==sha(D/'GREEN'/n)==h,'actual master equals tested GREEN '+n)
need(len(source['whole_stage'])==542,'full tested stage')
for tree in ['src','test']:need({str(p.relative_to(M)) for p in (M/tree).rglob('*') if p.is_file()}=={n for n in source['whole_stage'] if n.startswith(tree+'/')},'whole source/test scope')
con=read(P/'contract.json');greencon=read(D/'GREEN-run/contract.json');green=read(D/'GREEN-run/result-review.json')
need(con['arm']=='MASTER' and con['source_root']==str(M) and con['files']==greencon['files'] and len(con['files'])==len(set(con['files']))==57,'same exact whole files')
need(con['expected_total']==green['total']==345121 and con['expected_exit']==con['expected_failures']==0 and con['expected_failure_locations']==[] and con['attempts']==1,'frozen all-pass outcome')
need(con['shared_limit_seconds']==3000 and con['guard_limit_seconds']==2992,'deadline')
wantcommand=[v.replace('--project='+str(D/'GREEN'),'--project='+str(M)).replace(str(D/'GREEN-run/tests.jl'),str(P/'tests.jl')) for v in greencon['command']]
need(con['command']==wantcommand,'exact actual-master command')
need((P/'tests.jl').read_text()==(D/'GREEN-run/tests.jl').read_text().replace(str(D/'GREEN'),str(M)).replace('GREEN','MASTER'),'driver only source/phase identity changes')
need((P/'launch.py').read_bytes()==(D/'GREEN-run/launch.py').read_bytes(),'same launcher')
for n in ['entry_gate.py','guard_reviewed.py','supervisor_reviewed.py']:need((P/'guard'/n).read_bytes()==(D/'GREEN-run/guard'/n).read_bytes(),'same guard '+n)
common=(D/'GREEN-run/common.py').read_text().replace("TARGET='"+BASE+"'","TARGET='"+TARGET+"'").replace("==git(['rev-parse','origin/master'])==TARGET","==TARGET and git(['rev-parse','origin/master'])=='"+BASE+"'")
need((P/'common.py').read_text()==common,'only reviewed actual-master ref transition')
OVERRIDES=['JULIA_PROJECT','JULIA_LOAD_PATH','JULIA_BINDIR','JULIA_CPU_TARGET','JULIA_DEPOT_PATH','LD_PRELOAD','LD_LIBRARY_PATH','LD_AUDIT','BASH_ENV','ENV','PYTHONPATH','PYTHONHOME']
need(all(not os.environ.get(k) for k in OVERRIDES),'environment override');need({k:os.environ[k] for k in OVERRIDES+['JULIA_NUM_THREADS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'] if k in os.environ}==read(P/'environment.json')['inherited'],'environment')
env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')
def git(*args,root=M):return subprocess.check_output(['/usr/bin/git','-C',str(root),*args],env=env).decode().strip()
need(git('rev-parse','HEAD')==git('rev-parse','master')==TARGET and git('rev-parse','origin/master')==BASE,'actual/tracking refs')
need(git('rev-parse','HEAD',root=R)=='c01e9376bdbcda7cb54ba55735cf053299b9af45','diagnostic HEAD')
need(git('rev-list','--parents','-n','1',TARGET)==TARGET+' '+BASE,'single parent fast forward')
commit=read(D/'production-commit.json');need(git('rev-parse',TARGET+'^{tree}')==commit['tree']=='138985a0853b03467c8b8014c77538579c581ddd','reviewed tree')
names=sorted(git('diff-tree','--no-commit-id','--name-only','-r',TARGET).splitlines());need(names==sorted(commit['names'])==sorted(source['names']) and len(names)==4,'only reviewed committed paths')
def tree(revision):
 out={}
 for line in git('ls-tree','-r','--full-tree',revision).splitlines():
  meta,name=line.split('\t',1);mode,kind,blob=meta.split();out[name]=(mode,kind,blob)
 return out
before=tree(BASE);after=tree(TARGET);expected=dict(before)
for n in names:need(after[n][2]==commit['blobs'][n],'reviewed blob '+n);expected[n]=after[n]
need(after==expected,'entire commit tree has no unrelated changes')
entries={}
for line in git('ls-files','--stage').splitlines():
 meta,n=line.split('\t',1);mode,blob,stage=meta.split();need(stage=='0','unmerged index');entries[n]=(mode,'blob',blob)
need(entries==after and not git('diff','--cached','--name-only') and not git('diff','--name-only','HEAD','--','src','test','Project.toml'),'actual current index and source match reviewed commit')
priorentries={}
for line in read(D/'integration-before.json')['entries']:
 if not line:continue
 meta,n=line.split('\t',1);mode,blob,stage=meta.split();need(stage=='0','before index stages');priorentries[n]=(mode,'blob',blob)
need(priorentries==before,'before index snapshot equals original parent')
need(read(D/'integration-after.json')==dict(fast_forward=True,protected_unchanged=True,pushed=False,target=TARGET,unrelated_indexes_unchanged=True),'recorded integration')
admission=read(P/'admission.json');audit=read(P/'audit.json')
for record in [admission,audit]:
 need(record['accepted'] is True,'accepted admission/audit')
 for n,h in record['bindings'].items():need(sha(n)==h,'actual result binding '+n)
need((P/'audit.py').read_bytes()==(D/'phase-audit-complete.py').read_bytes()==(D/'GREEN-run/audit.py').read_bytes(),'same previously reviewed postexit auditor')
process=read(P/'output/process.json');sup=read(P/'supervisor.json');done=read(P/'completed.json');inv=read(P/'invocation.json');res=read(P/'reservation.json');log=(P/'output/run.log').read_text()
need(process['reason']=='exit0' and process['returncode']==0 and process['pins_unchanged'] is True,'actual MASTER child pass')
need(sup['accepted'] is True and sup['returncode']==0 and not sup['soft_timeout'] and not sup['hard_timeout'] and not sup['abnormal_cleanup_attempted'] and not sup['child_cleanup_attempted'] and 'cleanup_error' not in sup,'normal supervisor completion')
need(done['accepted'] is True and done['pins_unchanged'] is True and done['limit_seconds']==3000 and done['elapsed_shared_seconds']<=3000 and sup['elapsed_seconds']<=3000 and process['elapsed_including_launch']<=2992,'inclusive guarded deadlines')
need(process['command']==con['command']==inv['Julia_command'] and process['pins_sha256']==sha(P/'pins.json')==res['pins_sha256'],'command/pin chain')
need(res['attempt']==1 and res['admission_sha256']==sha(P/'admission.json') and res['guard_deadline']==res['started_monotonic']+2992 and res['outer_deadline']==res['started_monotonic']+3000,'one reservation and admission deadlines')
need(inv['common_started']==res['started_monotonic'] and inv['guard_deadline']==res['guard_deadline'] and inv['outer_deadline']==res['outer_deadline'],'invocation deadlines')
need(sup['guard_identity']['command']==' '.join(inv['command'])+' ','actual guard command')
gate=read(P/'output/gate.json');cur=read(P/'output/current.json');permit=read(P/'output/permit.json')
need(process['runner']==sup['guard_identity']==cur['runner']==gate['parent'] and process['child']==cur['child']==gate['identity'],'runner/child identity linkage')
need(gate['command']==cur['command']==permit['command']==con['command'] and gate['parent_death_signal']==9 and gate['monotonic_ready']<res['guard_deadline'],'entry signal/command/deadline')
need(gate['current_sha256']==sha(P/'output/current.json')==permit['current_sha256'] and gate['permit_sha256']==sha(P/'output/permit.json') and sha(P/'output/pins.json')==sha(P/'pins.json'),'gate hashes and copied pins')
need(re.findall(r'^SRG_SOURCE (.*)$',log,re.M)==[str(M/'src/JSimplex.jl')] and re.findall(r'^INCLUDING (.*)$',log,re.M)==con['files'],'actual source and exact57ordered includes')
need(not re.search(r'^ERROR:',log,re.M) and 'Test Failed at ' not in log and 'Error During Test' not in log,'no uncaught or test errors')
headers=re.findall(r'^Test Summary:.*?\|\s*(.*?)$',log,re.M);need(len(headers)==1 and headers[0].split()==['Pass','Total','Time'],'strict ordinary summary/no skips or broken')
roots=re.findall(r'^Sum rational growth MASTER\s*\|\s*(\d+)\s+(\d+)\s+[^\n]+$',log,re.M);need(roots==[('345121','345121')],'exact frozen ordinary assertion totals')
need(log.count('SRG_COMPLETED MASTER')==1,'single successful completion')
need(audit['arm']=='MASTER' and audit['expected_failures']==0 and audit['passed']==audit['total']==admission['expected_total']==con['expected_total']==345121 and audit['elapsed_shared_seconds']==done['elapsed_shared_seconds'],'audit corroborates raw frozen outcome')
resources=[json.loads(line) for line in (P/'output/resources.jsonl').read_text().splitlines()];need(len(resources)==audit['samples']==1901,'all recorded resource samples')
need(all(type(x['elapsed']) in [int,float] and math.isfinite(x['elapsed']) and 0<=x['elapsed']<2992 and x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources),'resource/time limits')
need(all(resources[i]['elapsed']<resources[i+1]['elapsed'] for i in range(len(resources)-1)),'resource observation order')
minimum_ram=min(x['available_kib'] for x in resources);maximum_swap=max(x['swap_used_kib'] for x in resources)
need(minimum_ram==audit['minimum_available_kib']==18651868 and maximum_swap==audit['maximum_swap_kib']==0,'resource extrema')
need(process['terminal_memory']['available_kib']>=6*1024**2 and process['terminal_memory']['swap_used_kib']<=1024**2,'terminal resources')
peaks=[int(v.split()[1]) for x in resources for v in x.get('child_memory',[]) if v.startswith('VmPeak:')];need(peaks and max(peaks)<8*1024**2,'sampled address-space peaks')
need(process['child_maxrss_kib']==audit['child_maxrss_kib']==3973672,'child RSS accounting')
for name in ['host-after.json','audit-host.json']:need(len(read(P/name)['groups'])==659 and read(P/name)['no_Julia'] is True,'recorded full closure')
seed=read(P/'host-seed.json');runids={process[k][v] for k in ['runner','child'] for v in ['pgid','sid']};groups=set(seed['groups'])|runids;historical=set(read(D/'host-seed.json')['groups'])
for name in ['output/process.json','correctness-qualification/output/process.json','RED-run/output/process.json','GREEN-run/output/process.json']:
 p=read(D/name);historical.update(p[k][v] for k in ['runner','child'] for v in ['pgid','sid'])
historical.update(runids);need(len(seed['groups'])==657 and groups==historical and len(groups)==659,'complete historical groups')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==seed['boot_id'],'boot');allowance=R/'diagnostics/generic-quality-local/2026-10-27/host-identity-allowance.json';need(sha(allowance)=='f0b6a5093b9c1875ec8718bca8775bc44ba4d6d6ab98a1ac23adfe52d69f2a92','fixed allowance');allowed=read(allowance)['identities'];processes=[];collisions=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  fields=(p/'stat').read_text().rsplit(')',1)[1].split();cmd=[x.decode(errors='replace') for x in (p/'cmdline').read_bytes().split(b'\0') if x];comm=(p/'comm').read_text().strip();ident=dict(pid=int(p.name),pgid=int(fields[2]),sid=int(fields[3]),start_ticks=int(fields[19]),command=cmd,boot_id=boot)
  need(not any(Path(x).name.lower().startswith('julia') for x in [comm]+cmd[:1]),'live Julia')
  if ident['pgid'] in groups or ident['sid'] in groups:need(ident in allowed,'historical group/session collision');collisions.append(ident)
  processes.append(ident)
 except (FileNotFoundError,ProcessLookupError):pass
mem={v.split(':')[0]:int(v.split()[1]) for v in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'RAM/swap')
put('independent-result-host.json',dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=processes,collisions=collisions,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']))
report="""# Independent actual-master result: accepted

Actual master bb765d008c6e8aab6187aa0ea49d49a4f8a03309 passed345,121/345,121 ordinary Test assertions across exactly the same57 complete files in the same order as GREEN. The raw log identifies /home/jspitz/JSimplex.jl/src/JSimplex.jl, contains one strict Pass/Total/Time root summary and one successful MASTER completion, with no test failure, error, broken/skipped outcome or uncaught ERROR. The frozen GREEN assertion total is matched exactly.

Raw child/guard/supervisor/reservation/invocation/permit/current/gate records independently agree on the admitted command, source project, identities, boot/start ticks/commands, parent-death signal9 and pin hashes. Child and supervisor exited0 normally without timeout or abnormal cleanup. The single run finished in1903.905231521 shared seconds within3000, with the child inside the2992 guard deadline. All1,901 ordered resource samples passed: minimum available RAM18,651,868 KiB, maximum swap0. Child maximum RSS was3,973,672 KiB, with sampled maximum virtual peak4,548,160 KiB below the8GiB address-space cap. The2GiB setting is a heap hint rather than an RSS cap; these observations do not prove native retained-memory freedom.

All838 current pins/resolved paths and full source/test membership remain unchanged. The actual542-file source/test/environment snapshot still equals the tested GREEN snapshot. Read-only Git checks reproduce the reviewed single-parent commit, complete tree138985a0853b03467c8b8014c77538579c581ddd, exact four-path change set and current index entries. HEAD/master remain bb765d00; origin/master remains the old ce5d4a74 because no push has yet occurred. No unrelated tree/index or protected user-file change was found.

Historical before mappings and every earlier case inventory were independently rechecked without rewriting old pins: the three replaced source/test files and original master-index bytes remain preserved, and the one added test is explicitly accounted for. Old failed comparison, decoder qualification, rejected audits, original RED and all-pass GREEN evidence remain intact. The post-exit MASTER auditor is byte-identical to the previously reviewed complete phase auditor, with no retroactive launch pin. Current independent closure checks all659 historical identifiers as groups AND sessions with boot/start-ticks/commands and only the fixed unrelated allowance; no Julia is active, and environment/refs/resources/protected state agree.

No production change beyond the already reviewed A/B/C edits appeared during actual-master validation. No unnecessary new scan, solve, copy, numerical cache or retained buffer was found; numerical guards, precision/tolerance rules, ownership and exception semantics remain as previously reviewed and tested. This result is mandatory actual-commit validation, not another benchmark or proof of full-suite, end-to-end speed, large-problem, x64 or native-memory behavior.

The actual-master result is accepted and satisfies the remaining test gate for the planned normal non-force publication of this reviewed commit, subject to the existing final unchanged-state/publication checks and remote verification. The reviewer performed no Julia execution, old auditor/launcher rerun, Git mutation or push.
"""
with (P/'RESULT-REVIEW.md').open('x') as f:f.write(report)
paths=[P/n for n in ['admission.json','audit.json','audit.py','contract.json','pins.json','tests.jl','common.py','protected-before.json','output/run.log','output/process.json','output/resources.jsonl','output/gate.json','output/current.json','output/permit.json','output/pins.json','supervisor.json','completed.json','reservation.json','invocation.json','host-after.json','audit-host.json','independent-result-review.py','independent-result-host.json','RESULT-REVIEW.md']]+[D/n for n in ['production-commit.json','commit-review.json','source-inverse.json','integration-before.json','integration-after.json','integration-historical-path-map.json','GREEN-run/result-review.json','phase-audit-complete.py']]
put('result-review.json',dict(accepted=True,findings=[],bindings={str(p):sha(p) for p in paths},arm='MASTER',commit=TARGET,parent=BASE,tree=commit['tree'],passed=345121,total=345121,expected_failures=0,whole_files=57,pins=838,elapsed_shared_seconds=done['elapsed_shared_seconds'],resource_samples=1901,minimum_available_kib=minimum_ram,maximum_swap_kib=maximum_swap,child_maxrss_kib=process['child_maxrss_kib'],historical_groups_and_sessions=659,normal_nonforce_push_authorized=True,remote_verification_required=True,Julia_executed=False,Git_mutated=False,old_scripts_executed=False))
print(json.dumps(dict(accepted=True,findings=0,commit=TARGET,passed=345121,whole_files=57,pins=838,elapsed_shared_seconds=done['elapsed_shared_seconds'],historical_groups_and_sessions=659)))
