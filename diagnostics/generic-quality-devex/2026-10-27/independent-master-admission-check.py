from pathlib import Path
import json,hashlib,subprocess,os,datetime,ast
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-devex/2026-10-27');Q=D/'MASTER-run';M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2];S=D/'GREEN';target='ca64312f7f74b1d7bec047718399f229674b3e1d';base='7e306e24f064a8aa214bc88379e059def77661ab'
def need(v,m):
 if not v:raise RuntimeError(m)
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def git(*a,env=None):return subprocess.check_output(['git','-C',str(M),*a],env=env or dict(os.environ,GIT_OPTIONAL_LOCKS='0'))
def g(*a):return git(*a).decode().strip()
def put(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
co=read(D/'commit-review.json');need(co['accepted'] and co['findings']==[] and co['commit']==target and co['parent']==base,'commit review')
for n,h in co['bindings'].items():need(sha(Path(n))==h,'commit binding '+n)
# Do not revalidate old pre-integration pin paths against their historical content; inspect preserved beforeimages instead.
green=read(D/'GREEN-run/result-review.json');need(green['accepted'] and green['findings']==[] and green['passed']==green['total']==186622,'GREEN acceptance')
for ref in ['HEAD','master', 'refs/heads/codex/generic-quality-devex']:need(g('rev-parse',ref)==target,'target ref')
need(g('rev-parse','origin/master')==base and g('branch','--show-current')=='master','tracking base')
need(g('rev-parse',target+'^{tree}')==co['tree'] and g('rev-list','--parents','-n','1',target).split()==[target,base],'immutable commit/tree')
for tree in ['src','test']:
 paths={str(p.relative_to(M)) for p in (M/tree).rglob('*') if p.is_file()};need(paths=={n for n in co['actual_commit_sha256'] if n.startswith(tree+'/')},'actual tree membership')
 for n in paths:need(sha(M/n)==sha(S/n)==co['actual_commit_sha256'][n],'actual committed/tested '+n)
need(not g('diff','--name-only','HEAD','--','src','test','Project.toml'),'production clean')
hist=read(D/'integration-historical-path-map.json');oldprot=read(D/'protected-before.json');prot=read(Q/'protected-before.json');baseline=read(D/'baseline-tree.json');names=co['names']
need(hist['master_before']==base and hist['older_maps_preserved'],'history base')
need(set(hist['source_before'])=={str(M/n) for n in names if n in baseline},'exact before paths')
for n,v in hist['source_before'].items():rel=str(Path(n).relative_to(M));need(v['before']==str(D/'baseline'/rel) and v['sha256']==baseline[rel]==sha(Path(v['before'])),'preserved source')
idx=g('rev-parse','--path-format=absolute','--git-path','index');need(set(hist['master_index_before'])=={idx},'before index path');before=hist['master_index_before'][idx];need(before['before']==str(D/'before-master/master.index') and before['sha256']==oldprot['indexes'][idx]==sha(Path(before['before'])),'before index bytes')
oldentries=git('ls-files','--stage','-z',env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_INDEX_FILE=before['before']));entries=git('ls-files','--stage','-z');integration=read(D/'integration-before.json')
need(oldentries.decode().split('\0')==integration['entries'],'original entries')
def unrelated(b):return [v for v in b.decode().split('\0') if v and v.split('\t',1)[1] not in names]
need(unrelated(oldentries)==unrelated(entries),'unrelated index entries preserved');need(git('diff','--cached','--raw','-z').decode()==integration['staged'],'staged state preserved')
need(prot['files']==oldprot['files'] and set(prot['indexes'])==set(oldprot['indexes']),'protection membership')
for n,h in prot['files'].items():need(sha(Path(n))==h,'protected file')
for n,h in prot['indexes'].items():need(sha(Path(n))==h and (n==idx or h==oldprot['indexes'][n]),'protected index')
pins=read(Q/'pins.json');originalpins=read(Q/'pins.json.before-time')
expected_new={str(D/'MASTER-TIME-ADDENDUM.md'),str(D/'prepare-master-time.py')};need(set(pins['inventory'])-set(originalpins['inventory'])==expected_new and set(originalpins['inventory'])<=set(pins['inventory']),'only timer pin additions')
changed={n for n in originalpins['inventory'] if originalpins['inventory'][n]!=pins['inventory'][n]};need(changed=={str(Q/n) for n in ['contract.json','launch.py','audit.py']},'only timer pin changes')
for n,v in pins['inventory'].items():p=Path(n);need(str(p.resolve(strict=True))==v['resolved'] and sha(p)==v['sha256'],'latest pin '+n)
for tree in pins['trees']:need({str(p) for p in Path(tree).rglob('*') if p.is_file()}=={n for n in pins['inventory'] if Path(n).is_relative_to(tree)},'pin tree membership')
for n in ['contract.json','launch.py','audit.py']:need(sha(Q/(n+'.before-time'))==originalpins['inventory'][str(Q/n)]['sha256'],'original timer evidence')
for n in ['launch.py','audit.py']:
 old=(Q/(n+'.before-time')).read_text();new=(Q/n).read_text();need(new==old.replace('1800','2400').replace('1792','2392'),'only cap replacement '+n);need(old==(D/'GREEN-run'/n).read_text(),'unchanged prior launch/audit');ast.parse(new)
c=read(Q/'contract.json');oldc=read(Q/'contract.json.before-time');expected=dict(oldc,shared_limit_seconds=2400,guard_limit_seconds=2392);need(c==expected,'only contract cap')
gc=read(D/'GREEN-run/contract.json');need(c['files']==gc['files'] and len(c['files'])==34 and c['expected_total']==186622 and c['expected_failures']==c['expected_exit']==0 and c['expected_failure_locations']==[] and c['attempts']==1,'exact allpass expected cases')
need(c['source_root']==str(M) and c['command']==[a.replace(str(D/'GREEN-run'),str(Q)).replace('--project='+str(S),'--project='+str(M)) for a in gc['command']],'actual M command')
need((Q/'tests.jl').read_text()==(D/'GREEN-run/tests.jl').read_text().replace(str(S),str(M)).replace('Quality Devex GREEN','Quality Devex MASTER').replace('COMPLETED GREEN','COMPLETED MASTER'),'ordinary actual M driver')
for n in ['entry_gate.py','guard_reviewed.py','supervisor_reviewed.py']:need((Q/'guard'/n).read_bytes()==(D/'GREEN-run/guard'/n).read_bytes(),'identical guarded runtime')
expectedcommon=(D/'GREEN-run/common.py').read_text().replace("TARGET='"+base+"'","TARGET='"+target+"'").replace("git(['rev-parse','HEAD'])==git(['rev-parse','master'])==git(['rev-parse','origin/master'])==TARGET","git(['rev-parse','HEAD'])==git(['rev-parse','master'])==TARGET and git(['rev-parse','origin/master'])=='"+base+"'")
need((Q/'common.py').read_text()==expectedcommon,'only actual master refs in common')
need(not (Q/'output').exists() and not (Q/'reservation.json').exists(),'exclusive first attempt')
seed=read(Q/'host-seed.json');need(seed==read(D/'GREEN-run/audit-host.json'),'continuous host history');groups=set(seed['groups']);need(len(groups)==583,'all groups');processes=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  st=(p/'stat').read_text().rsplit(')',1)[1].split();a=[v.decode(errors='replace') for v in (p/'cmdline').read_bytes().split(b'\0') if v];comm=(p/'comm').read_text().strip();pgid,sid=int(st[2]),int(st[3]);need(pgid not in groups and sid not in groups,'historical group/session');need(not any(Path(v).name.lower().startswith('julia') for v in [comm]+a[:1]),'Julia active');processes.append(dict(pid=int(p.name),pgid=pgid,sid=sid,start_ticks=int(st[19]),command=a))
 except (FileNotFoundError,ProcessLookupError):pass
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==seed['boot_id'],'same boot');mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'fresh memory')
put(Q/'independent-admission-host.json',dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=processes,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']))
report='''Verdict: ACCEPTED for one fresh actual-MASTER attempt, inclusive 2400 seconds and guard cutoff 2392 seconds. No unresolved findings. This is prospective launch admission, not permission to accept a failed test or publish without independent result review.

Actual /home/jspitz/JSimplex.jl HEAD/master equals ca64312f7f74b1d7bec047718399f229674b3e1d; origin/master remains the reviewed parent 7e306e24f064a8aa214bc88379e059def77661ab. All 532 actual source/test files and complete membership match the reviewed commit hashes and tested GREEN bytes. Existing tests, numerical thresholds and generic fallbacks remain unchanged. The sole parent/tree and prior independent commit/GREEN reviews are verified. Original changed-source beforeimages and original master index bytes remain preserved. A read-only examination of the before index and current index confirms unrelated entries and staged state unchanged; protected user files and diagnostic index match their originals.

The new contract selects exactly the same 34 ordinary files and requires 186622 passes, zero failures/errors/broken/skips and exit zero. Actual package/project identity and single Julia/BLAS thread assertions are retained. No new test case, warmup, precision, allocation tolerance, numerical retry or release exception was introduced. The historical Rational gate must pass anew; any failure remains evidence and requires a separate disposition.

The prospective timer amendment is justified by the witnessed 1533.55-second GREEN run and the supplied standing human instruction to allow tests more time. The original pre-amendment contract/launch/audit/pins are preserved. Independent text and dictionary comparisons confirm that launch/audit change only 1800 to 2400 and 1792 to 2392, and that the contract changes only those two caps. The latest pin manifest updates only those three inputs and adds the addendum/preparer. Guard, entry gate and supervisor bytes are identical to GREEN; their dynamic inclusive outer limit receives 2400 and their child guard receives 2392 minus preparation elapsed. Prelaunch, execution, cleanup and final checks share that same budget. All other resource/ownership checks remain: Julia/BLAS1, GC1,0, heap2GiB hint, AS8GiB, RAMavailable6GiB, swap1GiB, entry permit and parent-death, process identity and owned cleanup.

Every latest inventory entry and all complete pin trees were independently checked. Fresh host evidence verifies all 583 historical groups AND sessions absent, boot/start ticks/commands, no live Julia and adequate memory. Launch must refresh these conditions and refuse drift or an existing attempt. The reviewer ran no Julia and made no production/source/index/ref change. Normal nonforce publication still requires actual-master all-pass evidence and independent outcome acceptance, plus the preserved history/tested-tree checks.
'''
with (Q/'ADMISSION-REVIEW.md').open('x') as f:f.write(report)
files=[p for p in Q.rglob('*') if p.is_file()]+[D/n for n in ['commit-review.json','COMMIT-REVIEW.md','GREEN-run/result-review.json','GREEN-run/RESULT-REVIEW.md','MASTER-TIME-ADDENDUM.md','prepare-master-time.py','integration-before.json','integration-after.json','integration-historical-path-map.json','source-inverse.json','independent-master-admission-check.py']]
put(Q/'admission.json',dict(accepted=True,findings=[],attempts=1,expected_failures=0,expected_total=186622,shared_limit_seconds=2400,guard_limit_seconds=2392,inventory_entries=len(pins['inventory']),review=str(Q/'ADMISSION-REVIEW.md'),bindings={str(p):sha(p) for p in files}))
print(json.dumps(dict(accepted=True,inventory_entries=len(pins['inventory']),source_test_files=len(co['actual_commit_sha256']),historical_groups=len(groups),sha256=sha(Q/'admission.json'))))
