from pathlib import Path
import os,sys,json,hashlib,re,math,subprocess,datetime
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-sum-rational-growth/2026-10-28');P=D/'GREEN-run';S=D/'GREEN';M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2]
BASE='ce5d4a74019e0dc2e656d08161641c498b159e7b';HEAD='c01e9376bdbcda7cb54ba55735cf053299b9af45';os.environ['GIT_OPTIONAL_LOCKS']='0'
def need(v,m):
 if not v:raise RuntimeError(m)
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,s):
 with Path(p).open('x') as f:f.write(s)
def put(p,v):save(p,json.dumps(v,indent=2,sort_keys=True)+'\n')
def g(a,root=M):return subprocess.check_output(['/usr/bin/git','-C',str(root),*a]).decode().strip()
def accepted(path):
 r=read(path);need(r['accepted'] is True and r.get('findings',[])==[],'accepted '+str(path))
 for n,h in r['bindings'].items():need(sha(n)==h,'review/audit binding '+n)
 return r
def numeric(x):return type(x) in [int,float] and math.isfinite(x)
script=P/'independent-result-review.py';save(script,Path(__file__).read_text())
admission=accepted(P/'admission.json');production=accepted(D/'production-review.json');red=accepted(D/'RED-run/result-review.json');cost=accepted(D/'result-review.json');qualification=accepted(D/'correctness-qualification/result-review.json');audit=accepted(P/'audit.json')
need(cost['original_run_accepted'] is False and cost['accepted_variants']==['A','B','C'],'qualified costs and original failure preserved')
c=read(P/'contract.json');pins=read(P/'pins.json');p=read(P/'output/process.json');sup=read(P/'supervisor.json');done=read(P/'completed.json');reserve=read(P/'reservation.json');invoke=read(P/'invocation.json');gate=read(P/'output/gate.json');current=read(P/'output/current.json');permit=read(P/'output/permit.json');log=(P/'output/run.log').read_text()
need(c['arm']=='GREEN' and c['attempts']==1 and c['expected_exit']==c['expected_failures']==0 and c['expected_failure_locations']==[],'one admitted zero-failure GREEN')
need(c['shared_limit_seconds']==3000 and c['guard_limit_seconds']==2992 and c['source_root']==str(S),'concrete source and shared budget')
prior=read(D.parents[1]/'generic-bounds-norm-infeasibility/2026-10-27/GREEN-run/contract.json')['files']
files=['generic_sum_rational_growth_tests.jl']+prior+['refactorization_policy_tests.jl','refactorization_safety_tests.jl','refactorization_timing_tests.jl','refactorization_factor_tests.jl','refactorization_failure_tests.jl']
need(len(files)==len(set(files))==57 and c['files']==files,'all 57 exact whole files')
cmd=read(D/'contract-ready.json')['command'][:-2]+[str(P/'tests.jl')];cmd=[x.replace('--project='+str(M),'--project='+str(S)) for x in cmd]
need(c['command']==admission['command']==p['command']==invoke['Julia_command']==gate['command']==permit['command']==current['command']==cmd,'all command bindings')
need(p['cwd']==str(M) and type(p['returncode']) is int and p['returncode']==0 and p['reason']=='exit0' and p['pins_unchanged'] is True,'clean child completion')
need(read(P/'guard.log')==p,'raw guard record equals process record')
need(sup['accepted'] is True and type(sup['returncode']) is int and sup['returncode']==0,'supervisor accepted')
for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill','abnormal_cleanup_attempted','child_cleanup_attempted']:need(sup[k] is False,'no abnormal cleanup '+k)
need('cleanup_error' not in sup and done['accepted'] is True and done['pins_unchanged'] is True,'normal inclusive completion')
for value in [done['elapsed_shared_seconds'],sup['elapsed_seconds'],p['elapsed_including_launch']]:need(numeric(value) and 0<value<=3000,'bounded finite elapsed')
need(p['elapsed_including_launch']<=sup['elapsed_seconds']<=done['elapsed_shared_seconds'],'inclusive elapsed nesting')
need(done['limit_seconds']==reserve['limit_seconds']==3000 and reserve['attempt']==1,'reserved one3000 attempt')
need(reserve['guard_deadline']==reserve['started_monotonic']+2992 and reserve['outer_deadline']==reserve['started_monotonic']+3000,'absolute shared deadlines')
need(invoke['common_started']==reserve['started_monotonic'] and invoke['guard_deadline']==reserve['guard_deadline'] and invoke['outer_deadline']==reserve['outer_deadline'],'invocation shares exact clock')
need(reserve['admission_sha256']==sha(P/'admission.json') and reserve['pins_sha256']==p['pins_sha256']==sha(P/'pins.json'),'reserved admission/pins')
need(sha(P/'output/pins.json')==sha(P/'pins.json'),'raw copied pins')
need(gate['identity']==p['child']==current['child'] and gate['parent']==p['runner']==current['runner']==sup['guard_identity']==sup['guard_initial_identity'],'all actual process identities')
for role in ['runner','child']:
 ident=p[role];need(ident['pid']==ident['pgid']==ident['sid'] and all(type(ident[k]) is int and ident[k]>0 for k in ['pid','pgid','sid','start_ticks']) and ident['command'],'owned session leader '+role)
need(p['runner']['pid']!=p['child']['pid'] and p['runner']['boot_id']==p['child']['boot_id'],'distinct same-boot owners')
need(p['runner']['command']==' '.join(invoke['command'])+' ' and p['child']['command']==' '.join(p['gate_command'])+' ','actual startup command identities')
need(gate['parent_death_signal']==9 and gate['current_sha256']==permit['current_sha256']==sha(P/'output/current.json') and gate['permit_sha256']==sha(P/'output/permit.json'),'parent-death handshake hash links')
need(numeric(gate['monotonic_ready']) and reserve['started_monotonic']<gate['monotonic_ready']<reserve['guard_deadline'],'gate within deadline')
need(re.findall(r'^SRG_SOURCE (.*)$',log,re.M)==[str(S/'src/JSimplex.jl')],'one actual source identity')
need(re.findall(r'^INCLUDING (.*)$',log,re.M)==files,'57 actual ordered complete includes')
need(re.findall(r'^SRG_COMPLETED (.*)$',log,re.M)==['GREEN'],'one ordinary successful completion')
need(not re.search(r'Test Failed at |Error During Test|^ERROR:',log,re.M),'no test or uncaught runtime errors')
headers=re.findall(r'^Test Summary:.*\|\s*(.*)$',log,re.M);need(headers==['Pass   Total      Time'],'strict ordinary all-pass schema')
roots=re.findall(r'^Sum rational growth GREEN\s*\|\s*(\d+)\s+(\d+)\s+(\S+)\s*$',log,re.M);need(len(roots)==1,'one root summary')
passed,total=int(roots[0][0]),int(roots[0][1]);need(passed==total==345121,'exact complete raw all-pass count')
resources=[json.loads(line) for line in (P/'output/resources.jsonl').read_text().splitlines()];need(len(resources)==1925,'all 1925 resource samples')
last=-1.0
for r in resources:
 need(type(r['available_kib']) is int and r['available_kib']>=6*1024**2 and type(r['swap_used_kib']) is int and 0<=r['swap_used_kib']<=1024**2,'resource floor/ceiling')
 need(numeric(r['elapsed']) and last<r['elapsed']<p['elapsed_including_launch'],'ordered in-run resource time');last=r['elapsed']
 for field in r.get('child_memory',[]):
  match=re.fullmatch(r'(VmPeak|VmHWM|VmRSS|VmSwap):\s+(\d+) kB',field);need(match is not None,'typed child-memory sample')
  if match[1]=='VmPeak':need(int(match[2])<=8*1024**2,'sampled address-space bound')
need(p['terminal_memory']['available_kib']>=6*1024**2 and p['terminal_memory']['swap_used_kib']<=1024**2,'terminal resource bound')
minram=min(x['available_kib'] for x in resources);maxswap=max(x['swap_used_kib'] for x in resources)
need(minram==18767452 and maxswap==0 and type(p['child_maxrss_kib']) is int and p['child_maxrss_kib']==4027380,'independent resource values')
need(audit['passed']==audit['total']==passed and audit['expected_failures']==0 and audit['samples']==len(resources) and audit['minimum_available_kib']==minram and audit['maximum_swap_kib']==maxswap and audit['child_maxrss_kib']==p['child_maxrss_kib'] and audit['elapsed_shared_seconds']==done['elapsed_shared_seconds'],'independently reproduced standard audit')
need((P/'audit.py').read_bytes()==(D/'phase-audit-complete.py').read_bytes() and str(P/'audit.py') not in pins['inventory'],'separate reviewed postexit auditor not launch pin')
need(len(pins['inventory'])==1346 and set(pins['files'])==set(pins['inventory']),'exact 1346 pin inventory')
for n,v in pins['inventory'].items():need(str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'],'unchanged pin '+n)
for tree in pins['trees']:need({str(p) for p in Path(tree).rglob('*') if p.is_file()}=={n for n in pins['inventory'] if Path(n).is_relative_to(tree)},'complete pinned tree '+tree)
inv=read(D/'source-inverse.json');need(set(inv['whole_stage'])=={str(p.relative_to(S)) for p in S.rglob('*') if p.is_file()},'whole actual stage membership')
for n,h in inv['whole_stage'].items():need(sha(S/n)==h,'whole actual stage '+n)
changes=read(D/'changes.json')
for n in ['src/dual_simplex.jl','src/factorization.jl']:
 text=(S/n).read_text()
 for ch in reversed(changes):
  if ch['file']==n:need(text.count(ch['new'])==1,'exact staged replacement '+ch['variant']);text=text.replace(ch['new'],ch['old'])
 need(text==(D/'baseline'/n).read_text(),'full original source inverse '+n)
need(sha(S/'test/generic_sum_rational_growth_tests.jl')==sha(D/'new-test.jl')==sha(D/'RED/test/generic_sum_rational_growth_tests.jl'),'identical permanent gates after RED')
for n,h in read(D/'baseline-tree.json').items():need(sha(M/n)==sha(D/'baseline'/n)==h,'master remains original baseline '+n)
for root in [P,D]:
 protect=read(root/'protected-before.json')
 for n,h in {**protect['files'],**protect['indexes']}.items():need(sha(n)==h,'unchanged protected file/index '+n)
need(g(['rev-parse','HEAD'])==g(['rev-parse','master'])==g(['rev-parse','origin/master'])==BASE and g(['rev-parse','HEAD'],R)==HEAD,'unchanged actual refs')
need(not g(['diff','--name-only','HEAD','--','src','test','Project.toml']),'no production drift')
overrides=['JULIA_PROJECT','JULIA_LOAD_PATH','JULIA_BINDIR','JULIA_CPU_TARGET','JULIA_DEPOT_PATH','LD_PRELOAD','LD_LIBRARY_PATH','LD_AUDIT','BASH_ENV','ENV','PYTHONPATH','PYTHONHOME']
need(all(not os.environ.get(k) for k in overrides),'no unreviewed inherited environment')
need({k:os.environ[k] for k in overrides+['JULIA_NUM_THREADS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'] if k in os.environ}==read(P/'environment.json')['inherited'],'exact inherited environment')
# Fresh strict host closure with all historical groups AND sessions.
seed=read(P/'host-seed.json');groups=set(seed['groups'])
for path in D.rglob('output/process.json'):
 process=read(path)
 for role in ['runner','child']:
  for key in ['pgid','sid']:groups.add(process[role][key])
need(len(groups)==657 and groups==set(read(P/'audit-host.json')['groups'])==set(read(P/'host-after.json')['groups']),'complete657 historical groups')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==seed['boot_id']==p['runner']['boot_id'],'same boot')
allow=D.parents[1]/'generic-quality-local/2026-10-27/host-identity-allowance.json';need(sha(allow)=='f0b6a5093b9c1875ec8718bca8775bc44ba4d6d6ab98a1ac23adfe52d69f2a92','fixed exact unrelated identity allowance');permitted=read(allow)['identities'];processes=[];allowed_seen=[]
for proc in Path('/proc').glob('[0-9]*'):
 try:
  st=(proc/'stat').read_text().rsplit(')',1)[1].split();command=[v.decode(errors='replace') for v in (proc/'cmdline').read_bytes().split(b'\0') if v];comm=(proc/'comm').read_text().strip()
  ident=dict(pid=int(proc.name),pgid=int(st[2]),sid=int(st[3]),start_ticks=int(st[19]),boot_id=boot,command=command)
  need(not any(Path(v).name.lower().startswith('julia') for v in [comm]+command[:1]),'Julia still active')
  if ident['pgid'] in groups or ident['sid'] in groups:need(ident in permitted,'historical occupancy '+str(ident));allowed_seen.append(ident)
  processes.append(ident)
 except (FileNotFoundError,ProcessLookupError):pass
mem={line.split(':')[0]:int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'fresh resource headroom')
host=dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=processes,allowed_seen=allowed_seen,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'],observer_pid=os.getpid(),observer_parent_pid=os.getppid(),observer_command=sys.argv,refs=dict(master=BASE,diagnostic=HEAD));put(P/'independent-result-host.json',host)
report=f'''# Independent GREEN result review

Accepted:345,121/345,121 ordinary Test assertions passed across the exact57 admitted whole files. The raw log contains one actual staged source identity, all57 includes in order, one strict Pass/Total/Time root summary, one successful completion, and no test failures/errors or uncaught ERROR lines. The identical permanent regression that produced original RED28,316 passes plus seven allocation failures now passes within this whole-file run. Existing tests and thresholds are unchanged.

Independent checks reproduced the standard audit from raw process, gate, permit, current identity, supervisor, reservation, invocation, resource and Test records. The exact admitted command/project/source, source-resolving driver, single Julia/BLAS thread and GC1,0 settings remain pinned. Entry identities/boot/start_ticks/commands and current/permit hashes match; the parent-death signal is9. Child and supervisor exited0 normally, with no timeout, signal, cleanup error or abnormal cleanup. The run used one reservation and finished in{done['elapsed_shared_seconds']:.9f}s inclusive, within the shared3000-second allowance and2992-second guard deadline.

All1,925 ordered resource samples passed the6GiB available-RAM floor and1GiB swap ceiling; minimum available memory was18,767,452KiB and maximum swap0. Child maximum RSS was4,027,380KiB; sampled virtual peaks remained below8GiB. The2GiB setting is a heap-size hint, not an RSS cap. Terminal resources also passed. These resource observations do not establish native retained-memory freedom.

All1,346 launch pins, resolved paths and complete pinned source/test memberships remain unchanged. The whole actual GREEN stage matches the reviewed source-inverse inventory; exact inverse edits recover baseline, and the permanent test equals its RED/new-test copies. All master baseline source/test/environment bytes, protected user files/indexes and actual master/tracking/diagnostic refs remain unchanged. Fresh independent host closure checks all657 historical groups AND sessions with boot/start_ticks/command identity; no Julia is active and only the existing fixed exact unrelated identity allowance is permitted.

GREEN/audit.py is byte-identical to the separately reviewed complete postexit phase auditor and is explicitly not a retroactive launch pin. This independent review executed only new exclusive offline reviewer code, read-only Git/host checks and evidence reads; no Julia, old auditor/launcher import or rerun, measurement repeat or Git mutation occurred. The original comparison remains failed at111,259 passes plus90 decoder assertions; corrected qualification28,227 passes and separately qualified saved costs remain unchanged.

This accepts the concrete staged production result for the planned private-index commit. Actual commit review, fast-forward integration and a separately admitted actual-master run of these same57 files with frozen total345,121 remain required, followed by independent master-result review and normal publication checks. It is not full-suite, end-to-end-speedup, large-problem, x64 or native-retention qualification. CI/automation/HH state remains unchanged.
'''
md=P/'RESULT-REVIEW.md';save(md,report)
paths=[script,md,P/'independent-result-host.json']+[P/n for n in ['admission.json','contract.json','tests.jl','pins.json','audit.py','audit.json','audit-host.json','completed.json','supervisor.json','reservation.json','invocation.json','guard.log','host-after.json','launch-host.json','output/process.json','output/run.log','output/resources.jsonl','output/pins.json','output/current.json','output/permit.json','output/gate.json']]+[D/n for n in ['production-review.json','source-inverse.json','new-test.jl','test-gates.json','RED-run/result-review.json','result-review.json','correctness-qualification/result-review.json','phase-audit-complete.py']]+[S/n for n in inv['names']]
put(P/'result-review.json',dict(accepted=True,findings=[],arm='GREEN',passed=passed,total=total,expected_failures=0,whole_files=57,pins=1346,elapsed_shared_seconds=done['elapsed_shared_seconds'],resource_samples=len(resources),minimum_available_kib=minram,maximum_swap_kib=maxswap,child_maxrss_kib=p['child_maxrss_kib'],historical_groups_and_sessions=657,private_index_commit_authorized=True,integration_authorized=False,required_actual_MASTER_total=passed,Julia_executed=False,Git_mutated=False,old_scripts_executed=False,bindings={str(path):sha(path) for path in sorted(set(paths))}))
print(json.dumps(dict(accepted=True,arm='GREEN',passed=passed,total=total,whole_files=57,pins=1346,elapsed_shared_seconds=done['elapsed_shared_seconds'],historical_groups_and_sessions=657,Julia_executed=False,Git_mutated=False)))
