from pathlib import Path
import json,hashlib,re,subprocess,os,datetime,importlib.util
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-devex/2026-10-27');Q=D/'MASTER-run';M=Path('/home/jspitz/JSimplex.jl');S=D/'GREEN';target='ca64312f7f74b1d7bec047718399f229674b3e1d';base='7e306e24f064a8aa214bc88379e059def77661ab'
def need(v,m):
 if not v:raise RuntimeError(m)
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def git(*a,env=None):return subprocess.check_output(['git','-C',str(M),*a],env=env or dict(os.environ,GIT_OPTIONAL_LOCKS='0'))
def g(*a):return git(*a).decode().strip()
def put(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
pins=read(Q/'pins.json');need(len(pins['inventory'])==692,'pins count')
for n,v in pins['inventory'].items():p=Path(n);need(str(p.resolve(strict=True))==v['resolved'] and sha(p)==v['sha256'],'pin '+n)
for tree in pins['trees']:need({str(p) for p in Path(tree).rglob('*') if p.is_file()}=={n for n in pins['inventory'] if Path(n).is_relative_to(tree)},'complete pin membership')
need((Q/'pins.json').read_bytes()==(Q/'output/pins.json').read_bytes(),'copied pins')
for doc in [Q/'admission.json',Q/'audit.json',D/'commit-review.json',D/'publication-preparation-reviewed.json']:
 a=read(doc);need(a['accepted'] is True and a.get('findings',[])==[],'review '+str(doc))
 for n,h in a['bindings'].items():need(sha(Path(n))==h,'binding '+n)
co=read(D/'commit-review.json');green=read(D/'GREEN-run/result-review.json');need(co['commit']==target and co['parent']==base and green['accepted'] and green['findings']==[],'reviewed commit/GREEN')
for ref in ['HEAD','master','refs/heads/codex/generic-quality-devex']:need(g('rev-parse',ref)==target,'target ref')
need(g('rev-parse','origin/master')==base and g('branch','--show-current')=='master','unpublished tracking')
need(g('rev-parse',target+'^{tree}')==co['tree'] and g('rev-list','--parents','-n','1',target).split()==[target,base],'commit tree/parent')
for tree in ['src','test']:
 names={str(p.relative_to(M)) for p in (M/tree).rglob('*') if p.is_file()};need(names=={n for n in co['actual_commit_sha256'] if n.startswith(tree+'/')},'complete commit membership')
 for n in names:need(sha(M/n)==sha(S/n)==co['actual_commit_sha256'][n],'actual committed and tested bytes '+n)
need(not g('diff','--name-only','HEAD','--','src','test','Project.toml'),'production clean')
for group in read(Q/'protected-before.json').values():
 for n,h in group.items():need(sha(Path(n))==h,'protected '+n)
# Exercise the exact already-reviewed pre-push evidence checks on current read-only state.
spec=importlib.util.spec_from_file_location('quality_publication_checks',D/'publication_checks.py');pub=importlib.util.module_from_spec(spec);spec.loader.exec_module(pub)
pub.verify_tested_trees(M,S,pins,need,sha)
hist=read(D/'integration-historical-path-map.json');continuation=dict(master_source_before=hist['source_before'],master_index_before=hist['master_index_before']);pub.verify_historical_maps(D,M,g('rev-parse','--path-format=absolute','--git-path','index'),base,co['names'],hist,continuation,read(D/'protected-before.json'),read(D/'baseline-tree.json'),need,sha)
baseline=read(D/'baseline-tree.json');need(set(baseline)=={str(p.relative_to(D/'baseline')) for p in (D/'baseline').rglob('*') if p.is_file()},'baseline membership')
for n,h in baseline.items():need(sha(D/'baseline'/n)==h,'baseline before bytes')
log=(Q/'output/run.log').read_text();c=read(Q/'contract.json');need(c['arm']=='MASTER' and c['expected_total']==186622 and c['expected_failures']==c['expected_exit']==0 and c['expected_failure_locations']==[] and c['attempts']==1,'contract allpass')
need(c['files']==read(D/'GREEN-run/contract.json')['files'] and len(c['files'])==34,'same34')
need(re.findall(r'^INCLUDING (.*)$',log,re.M)==c['files'],'ordered raw includes')
headers=re.findall(r'^Test Summary:.*?\|(.*)$',log,re.M);need(len(headers)==1 and headers[0].split()==['Pass','Total','Time'],'ordinary no broken/skips/errors')
rows=re.findall(r'^Quality Devex MASTER\s*\|(.*)$',log,re.M);need(len(rows)==1 and rows[0].split()==['186622','186622','24m56.4s'],'actual raw total')
need(log.count('QUALITY_DEVEX_SOURCE '+str(M/'src/JSimplex.jl'))==1 and log.count('QUALITY_DEVEX_COMPLETED MASTER')==1,'source/completion')
for token in ['Test Failed at ','Error During Test','Test Broken','Some tests did not pass']:need(token not in log,'test failure token')
need(not re.search(r'^ERROR:',log,re.M),'top-level Julia error');need(all(line.startswith('[ Info: Restarting simplex on original LP after NUMERICAL_ERROR:') for line in log.splitlines() if 'ERROR:' in line),'only informational recovery errors')
p=read(Q/'output/process.json');gate=read(Q/'output/gate.json');cur=read(Q/'output/current.json');permit=read(Q/'output/permit.json');iv=read(Q/'invocation.json');s=read(Q/'supervisor.json');done=read(Q/'completed.json');res=read(Q/'reservation.json');audit=read(Q/'audit.json')
need(p['returncode']==0 and p['reason']=='exit0' and p['pins_unchanged'],'actual child exit')
need(p['command']==gate['command']==cur['command']==permit['command']==iv['Julia_command']==c['command'],'exact command')
need(p['runner']==gate['parent']==cur['runner']==s['guard_identity'] and p['child']==gate['identity']==cur['child'],'exact identities')
need(p['pins_sha256']==res['pins_sha256']==sha(Q/'pins.json') and res['admission_sha256']==sha(Q/'admission.json'),'reserved bindings')
need(gate['current_sha256']==permit['current_sha256']==sha(Q/'output/current.json') and gate['permit_sha256']==sha(Q/'output/permit.json') and gate['parent_death_signal']==9,'entry permit')
need(res['guard_deadline']==iv['guard_deadline']==res['started_monotonic']+2392 and res['outer_deadline']==iv['outer_deadline']==res['started_monotonic']+2400,'inclusive admitted deadline')
need(s['accepted'] and s['returncode']==0 and done['accepted'] and done['pins_unchanged'] and done['limit_seconds']==2400,'completion')
for key in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill','abnormal_cleanup_attempted','child_cleanup_attempted']:need(s[key] is False,'no timeout/cleanup '+key)
need('cleanup_error' not in s and p['elapsed_including_launch']<=s['elapsed_seconds']<=done['elapsed_shared_seconds']<2400,'duration')
resources=[json.loads(l) for l in (Q/'output/resources.jsonl').read_text().splitlines()];need(len(resources)==1499 and all(b['elapsed']>a['elapsed'] for a,b in zip(resources,resources[1:])),'all ordered samples')
minimum=min(x['available_kib'] for x in resources);maximum=max(x['swap_used_kib'] for x in resources);need(minimum==19741724 and maximum==0 and p['child_maxrss_kib']==3461796,'raw resource extrema')
need(p['terminal_memory']['available_kib']>=6*1024**2 and p['terminal_memory']['swap_used_kib']<=1024**2,'terminal resources')
need(audit['passed']==audit['total']==green['passed']==green['total']==186622 and audit['expected_failures']==0 and audit['elapsed_shared_seconds']==done['elapsed_shared_seconds'] and audit['samples']==len(resources) and audit['minimum_available_kib']==minimum and audit['maximum_swap_kib']==maximum,'auditor agrees with raw/GREEN')
for name in ['launch-host.json','host-after.json','audit-host.json']:
 h=read(Q/name);need(h['boot_id']==p['runner']['boot_id'] and h['no_Julia'],'saved host');groups=set(h['groups'])
 for proc in h['processes']:need(proc['pgid'] not in groups and proc['sid'] not in groups,'saved historical absence')
h=read(Q/'audit-host.json');groups=set(h['groups']);processes=[]
for proc in Path('/proc').glob('[0-9]*'):
 try:
  st=(proc/'stat').read_text().rsplit(')',1)[1].split();a=[x.decode(errors='replace') for x in (proc/'cmdline').read_bytes().split(b'\0') if x];comm=(proc/'comm').read_text().strip();pgid,sid=int(st[2]),int(st[3]);need(pgid not in groups and sid not in groups,'historical group/session active');need(not any(Path(x).name.lower().startswith('julia') for x in [comm]+a[:1]),'Julia active');processes.append(dict(pid=int(proc.name),pgid=pgid,sid=sid,start_ticks=int(st[19]),command=a))
 except (FileNotFoundError,ProcessLookupError):pass
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==h['boot_id'],'same boot');mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'fresh memory')
put(Q/'independent-result-host.json',dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=processes,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']))
report='''Verdict: actual MASTER ACCEPTED, no unresolved findings. The raw ordinary Test result is 186622 PASS / 186622 total across exactly the same 34 ordered files as GREEN, with zero failures, errors, broken tests or skips. Actual source identity is /home/jspitz/JSimplex.jl/src/JSimplex.jl, unique completion marker is present and child exit is zero. All prior thresholds, including the previously failing Rational allocation gate, pass anew unchanged; no old exception is used.

The independent offline review parsed the raw log, all 1499 ordered resource samples, process/guard/entry identity chain, parent-death and permit hashes, reservation/admission/copied pins, invocation and inclusive deadlines. It recomputed agreement with the auditor rather than relying on its verdict. Inclusive elapsed time is 1500.4778898909972 seconds under the admitted 2400-second cap; no timeout, kill, cleanup or retry occurred. Available memory stayed at least 19741724 KiB, swap remained zero, recorded child maximum RSS is 3461796 KiB. Informational NUMERICAL_ERROR recovery messages are solver logs, not ordinary Test or top-level Julia errors.

All 692 current pinned inputs and complete source/test memberships were independently rehashed. All 532 actual-master source/test files match the immutable reviewed commit ca64312f7f74b1d7bec047718399f229674b3e1d and the tested GREEN bytes. The full reviewed parent/tree, local HEAD/master/codex ref, still-unpublished origin/master parent, protected files/current indexes, preserved original source/master-index beforeimages and complete baseline remain valid. The already-reviewed publication helper's complete tested-tree and historical-map checks also pass on current state. Fresh host evidence verifies every historical group/session absent, same boot, process start ticks/commands, no live Julia and sufficient memory.

The exact production work/memory verdict remains: no unnecessary new full scans, solves, copies, conversions or retained roots; the reductions and three quality timing regressions remain as documented in the focused experiment. This 34-file correctness/regression run is not a new speed benchmark, full-suite/end-to-end claim, x64 qualification or native allocator/free measurement. The reviewer did not launch Julia, replay the auditor, or mutate source/index/ref. Normal nonforce publication of the reviewed exact commit may proceed under the existing publication script, which must recheck current tested/pinned trees, preserved evidence, approved origin and remote state immediately before pushing. Remote publication itself has not been performed by this review.
'''
with (Q/'RESULT-REVIEW.md').open('x') as f:f.write(report)
files=[p for p in Q.rglob('*') if p.is_file()]+[D/n for n in ['commit-review.json','COMMIT-REVIEW.md','GREEN-run/result-review.json','GREEN-run/RESULT-REVIEW.md','production-commit.json','source-inverse.json','baseline-tree.json','publication-preparation-reviewed.json','commit-integrate-publish.py','publication_checks.py','integration-historical-path-map.json','MASTER-TIME-ADDENDUM.md','independent-master-result-check.py']]
put(Q/'result-review.json',dict(accepted=True,findings=[],reviewer='independent production reviewer',commit=target,parent=base,passed=186622,total=186622,expected_failures=0,errors=0,broken=0,skipped=0,ordinary_files=34,inventory_entries=692,source_test_files=532,elapsed_shared_seconds=done['elapsed_shared_seconds'],minimum_available_kib=minimum,maximum_swap_kib=maximum,child_maxrss_kib=p['child_maxrss_kib'],review=str(Q/'RESULT-REVIEW.md'),bindings={str(f):sha(f) for f in files}))
print(json.dumps(dict(accepted=True,total=186622,elapsed=done['elapsed_shared_seconds'],historical_groups=len(groups),sha256=sha(Q/'result-review.json'))))
