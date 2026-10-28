from pathlib import Path
import json,hashlib,os,subprocess,datetime
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
need(not (P/'output').exists() and not (P/'reservation.json').exists(),'master attempt already reserved')
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
seed=read(P/'host-seed.json');groups=set(seed['groups']);historical=set(read(D/'host-seed.json')['groups'])
for name in ['output/process.json','correctness-qualification/output/process.json','RED-run/output/process.json','GREEN-run/output/process.json']:
 p=read(D/name);historical.update(p[k][v] for k in ['runner','child'] for v in ['pgid','sid'])
need(groups==historical and len(groups)==657,'complete historical groups')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==seed['boot_id'],'boot');allowance=R/'diagnostics/generic-quality-local/2026-10-27/host-identity-allowance.json';need(sha(allowance)=='f0b6a5093b9c1875ec8718bca8775bc44ba4d6d6ab98a1ac23adfe52d69f2a92','fixed allowance');allowed=read(allowance)['identities'];processes=[];collisions=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  fields=(p/'stat').read_text().rsplit(')',1)[1].split();cmd=[x.decode(errors='replace') for x in (p/'cmdline').read_bytes().split(b'\0') if x];comm=(p/'comm').read_text().strip();ident=dict(pid=int(p.name),pgid=int(fields[2]),sid=int(fields[3]),start_ticks=int(fields[19]),command=cmd,boot_id=boot)
  need(not any(Path(x).name.lower().startswith('julia') for x in [comm]+cmd[:1]),'live Julia')
  if ident['pgid'] in groups or ident['sid'] in groups:need(ident in allowed,'historical group/session collision');collisions.append(ident)
  processes.append(ident)
 except (FileNotFoundError,ProcessLookupError):pass
mem={v.split(':')[0]:int(v.split()[1]) for v in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'RAM/swap')
put('independent-host.json',dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=processes,collisions=collisions,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']))
report='''# Independent actual-master admission: accepted

The concrete actual-master command is admitted once against bb765d008c6e8aab6187aa0ea49d49a4f8a03309. HEAD and master equal that reviewed commit; origin/master remains ce5d4a74019e0dc2e656d08161641c498b159e7b, so no push has occurred. The commit has exactly that single parent and reviewed tree138985a0853b03467c8b8014c77538579c581ddd. Independent full-tree and index checks show exactly the four reviewed paths changed and no unrelated tree/index change. The actual source/test tree and all542 tested-stage files match GREEN byte-for-byte.

The driver resolves the actual /home/jspitz/JSimplex.jl project and loaded source. It includes the same57 complete files in the same order as accepted GREEN and requires frozen total345,121 with zero failures/errors/broken/skips and exit0. No file or threshold is removed. Command and driver changes from GREEN are limited to actual source/phase identity; launcher and guards are unchanged. MASTER common explicitly requires the new local commit and old remote-tracking commit and never invokes the old baseline unchanged check.

All838 current pins/resolved paths and complete source/test memberships were independently checked. Historical before maps preserve exactly the three replaced source/test files and the old master-index bytes. Every earlier case inventory is verified using those explicit before hashes, with the sole intentional new test accounted for in old master-test membership. Old admissions/results, failed comparisons and rejected audits remain unchanged. Protected user files retain their original hashes; the actual master index matches the reviewed target, its original bytes remain preserved, and unrelated indexes are unchanged.

Numerical/computational review remains the accepted exact A/B/C review: no new scan, basis solve, array copy, persistent numerical cache or retained buffer appears beyond the already reviewed edits. Numerical guards, precision/tolerance rules, ownership and exception behavior are retained. Prior source inverse, whole-function cost qualification, original RED and all-pass GREEN evidence bind the exact bytes now on master. The master run supplies location/commit validation; it is not a new benchmark or a claim of full-suite, x64, end-to-end speed or native retained-memory qualification.

Fresh actual-host closure verifies all657 historical identifiers as both groups AND sessions, exact boot/start ticks/commands, no Julia and only the fixed unrelated identity allowance. Environment and RAM/swap floors are unchanged. The command preserves one Julia/BLAS thread, GC1,0, compiled-modules existing, heap2G hint, AS8G cap, RAM6G/swap1G and owned-process guards. One shared3000-second budget and2992-second guarded deadline cover launch through closure. No MASTER reservation/output exists.

This offline review executed no Julia, old audit/launcher, Git mutation or push. Acceptance authorizes this one actual-master run only. Mandatory345,121 all-pass actual results, independent result review and normal publication checks remain required before push.
'''
with (P/'ADMISSION-REVIEW.md').open('x') as f:f.write(report)
paths=[P/n for n in ['pins.json','contract.json','tests.jl','common.py','launch.py','protected-before.json','guard/guard_reviewed.py','guard/supervisor_reviewed.py','guard/entry_gate.py','independent-admission.py','independent-host.json','ADMISSION-REVIEW.md']]+[D/n for n in ['production-commit.json','commit-review.json','source-inverse.json','production-review.json','integration-before.json','integration-after.json','integration-historical-path-map.json','GREEN-run/result-review.json','GREEN-run/contract.json','GREEN-run/audit.json']]
put('admission.json',dict(accepted=True,findings=[],bindings={str(p):sha(p) for p in paths},commit=TARGET,parent=BASE,tree=commit['tree'],pins=838,whole_files=57,expected_total=345121,expected_exit=0,expected_failures=0,historical_inventory_counts=historical_counts,historical_groups_and_sessions=657,push_authorized=False,Julia_executed=False,Git_mutated=False))
print(json.dumps(dict(accepted=True,findings=0,pins=838,commit=TARGET,whole_files=57,expected_total=345121,historical_groups_and_sessions=657)))
