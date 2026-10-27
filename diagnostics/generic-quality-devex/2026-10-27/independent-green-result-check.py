from pathlib import Path
import json,hashlib,re,subprocess,datetime,os
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-devex/2026-10-27');Q=D/'GREEN-run';M=Path('/home/jspitz/JSimplex.jl')
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def put(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
pins=read(Q/'pins.json');need(len(pins['inventory'])==1221,'inventory count')
for n,v in pins['inventory'].items():p=Path(n);need(str(p.resolve(strict=True))==v['resolved'] and sha(p)==v['sha256'],'pin '+n)
for tree in pins['trees']:need({str(p) for p in Path(tree).rglob('*') if p.is_file()}=={n for n in pins['inventory'] if Path(n).is_relative_to(tree)},'membership '+tree)
need((Q/'pins.json').read_bytes()==(Q/'output/pins.json').read_bytes(),'copied pins')
for doc in [D/'production-review.json',D/'publication-preparation-reviewed.json',Q/'admission.json',Q/'audit.json']:
 a=read(doc);need(a['accepted'] and a['findings']==[] if 'findings' in a else a['accepted'],'acceptance '+str(doc))
 for n,h in a['bindings'].items():need(sha(Path(n))==h,'binding '+n)
base=read(D/'baseline-tree.json');inv=read(D/'source-inverse.json');stage=D/'GREEN'
for n,h in base.items():need(sha(D/'baseline'/n)==sha(M/n)==h,'authoritative unchanged '+n)
need({str(p.relative_to(stage)):sha(p) for p in stage.rglob('*') if p.is_file()}==inv['whole_stage'],'whole tested stage')
for ref in ['HEAD','master','origin/master']:need(subprocess.check_output(['git','-C',str(M),'rev-parse',ref],text=True).strip()=='7e306e24f064a8aa214bc88379e059def77661ab','ref')
for group in read(Q/'protected-before.json').values():
 for n,h in group.items():need(sha(Path(n))==h,'protected '+n)
c=read(Q/'contract.json');log=(Q/'output/run.log').read_text();need(c['arm']=='GREEN' and c['expected_exit']==c['expected_failures']==0 and c['expected_failure_locations']==[],'allpass contract')
need(re.findall(r'^INCLUDING (.*)$',log,re.M)==c['files'] and len(c['files'])==34,'exact ordinary 34 files')
need(re.findall(r'^Test Summary:.*?\|(.*)$',log,re.M)==['   Pass   Total      Time'],'ordinary allpass schema')
need(re.findall(r'^Quality Devex GREEN\s*\|(.*)$',log,re.M)==[' 186622  186622  25m28.4s'],'ordinary raw total')
need(log.count('QUALITY_DEVEX_COMPLETED GREEN')==1 and log.count('QUALITY_DEVEX_SOURCE '+str(stage/'src/JSimplex.jl'))==1,'source/completion')
for token in ['Test Failed at ','Error During Test','ERROR:','Test Broken','Some tests did not pass'] :need(token not in log,'no failure token '+token)
# Both old/new ordinary tests still contain every original assertion; no skip/broken counting.
need((stage/'test/generic_quality_devex_tests.jl').read_bytes()==(D/'new-test.jl').read_bytes(),'new gates unchanged')
need((stage/'test/generic_residual_magnitudes_tests.jl').read_bytes()==(D/'baseline/test/generic_residual_magnitudes_tests.jl').read_bytes(),'prior Rational gate unchanged')
p=read(Q/'output/process.json');g=read(Q/'output/gate.json');cur=read(Q/'output/current.json');permit=read(Q/'output/permit.json');iv=read(Q/'invocation.json');s=read(Q/'supervisor.json');done=read(Q/'completed.json');reservation=read(Q/'reservation.json');audit=read(Q/'audit.json')
need(p['returncode']==0 and p['reason']=='exit0' and p['pins_unchanged'],'exit/pins')
need(p['command']==g['command']==cur['command']==permit['command']==iv['Julia_command']==c['command'],'command chain')
need(p['runner']==g['parent']==cur['runner']==s['guard_identity'] and p['child']==g['identity']==cur['child'],'identities')
need(p['pins_sha256']==reservation['pins_sha256']==sha(Q/'pins.json'),'pins hash')
need(reservation['admission_sha256']==sha(Q/'admission.json'),'admission hash')
need(g['parent_death_signal']==9 and g['current_sha256']==permit['current_sha256']==sha(Q/'output/current.json') and g['permit_sha256']==sha(Q/'output/permit.json'),'permit/parent death')
need(reservation['guard_deadline']==iv['guard_deadline']==reservation['started_monotonic']+1792 and reservation['outer_deadline']==iv['outer_deadline']==reservation['started_monotonic']+1800,'shared deadlines')
need(s['accepted'] and s['returncode']==0 and done['accepted'] and done['pins_unchanged'],'completed')
for key in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill','abnormal_cleanup_attempted','child_cleanup_attempted']:need(s[key] is False,'no timeout/cleanup '+key)
need('cleanup_error' not in s and p['elapsed_including_launch']<=s['elapsed_seconds']<=done['elapsed_shared_seconds']<1800,'inclusive duration')
resources=[json.loads(l) for l in (Q/'output/resources.jsonl').read_text().splitlines()];need(len(resources)==1532 and all(b['elapsed']>a['elapsed'] for a,b in zip(resources,resources[1:])),'ordered resource samples')
minimum=min(x['available_kib'] for x in resources);maximum=max(x['swap_used_kib'] for x in resources)
need(minimum==19776188 and maximum==0 and p['child_maxrss_kib']==3465444,'actual resource extrema')
need(p['terminal_memory']['available_kib']>=6*1024**2 and p['terminal_memory']['swap_used_kib']<=1024**2,'terminal memory')
need(audit['passed']==audit['total']==186622 and audit['expected_failures']==0 and audit['samples']==len(resources) and audit['minimum_available_kib']==minimum and audit['maximum_swap_kib']==maximum and audit['elapsed_shared_seconds']==done['elapsed_shared_seconds'],'auditor agrees with raw')
for name in ['launch-host.json','host-after.json','audit-host.json']:
 h=read(Q/name);need(h['boot_id']==p['runner']['boot_id'] and h['no_Julia'],'saved host');groups=set(h['groups'])
 for proc in h['processes']:need(proc['pgid'] not in groups and proc['sid'] not in groups,'saved historical absence')
h=read(Q/'audit-host.json');groups=set(h['groups']);processes=[]
for proc in Path('/proc').glob('[0-9]*'):
 try:
  st=(proc/'stat').read_text().rsplit(')',1)[1].split();a=[x.decode(errors='replace') for x in (proc/'cmdline').read_bytes().split(b'\0') if x];comm=(proc/'comm').read_text().strip();pgid,sid=int(st[2]),int(st[3])
  need(pgid not in groups and sid not in groups,'historical process active');need(not any(Path(x).name.lower().startswith('julia') for x in [comm]+a[:1]),'Julia active');processes.append(dict(pid=int(proc.name),pgid=pgid,sid=sid,start_ticks=int(st[19]),command=a))
 except (FileNotFoundError,ProcessLookupError):pass
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==h['boot_id'],'boot')
mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'fresh memory')
put(Q/'independent-result-host.json',dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=processes,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']))
report='''Verdict: GREEN ACCEPTED, with no unresolved findings. The actual ordinary Test summary is 186622 PASS / 186622 total across exactly the 34 contracted files, with zero failures, errors, broken tests or skips. The unique completion marker and expected zero child exit are present. All existing test files and thresholds remain unchanged, including the prior Rational allocation gate; its earlier exception is neither needed nor transferred. The six new whole-call allocation gates passed as part of the unchanged ordinary Test module.

The independent checker read the raw run.log and all 1532 resource samples, verified ordered includes, source/project assertions and completion, process/guard/entry identities, entry permit and parent-death binding, reservation/admission/copied pins, shared deadlines and zero timeout/cleanup indicators. Elapsed inclusive launch/guard time is 1533.551520326 seconds within the original 1800-second GREEN allowance. Minimum available RAM is 19776188 KiB, maximum swap zero and recorded child maximum RSS 3465444 KiB. These match the auditor, but acceptance was recomputed from raw data rather than inferred from its verdict.

All 1221 inventory entries were streamed through SHA256 again, including the independent RED result; complete source/test memberships and the entire staged candidate matched. The five candidate paths and all baseline source/test bytes still match the production review. Authoritative HEAD/master/origin/master remain 7e306e24f064a8aa214bc88379e059def77661ab. Protected files and indexes are unchanged. Fresh independent host evidence checks historical groups/sessions, boot/startticks/commands and absence of Julia. No Julia or historical auditor was rerun; no production file, index or ref was changed.

The production work/memory review remains applicable: no unnecessary new scans, solves, copies or retained roots, with measured local allocation/work reductions and documented quality timing regressions. This correctness/regression run is not a new speed benchmark, full-suite claim, x64 qualification or end-to-end throughput claim. Actual commit review and fresh actual-master all-pass qualification are still mandatory before publication. The prospective actual-master time allowance has no bearing on this completed GREEN result and must be bound by its own later admission.
'''
with (Q/'RESULT-REVIEW.md').open('x') as f:f.write(report)
files=[p for p in Q.rglob('*') if p.is_file()]+[D/'production-review.json',D/'PRODUCTION-REVIEW.md',D/'source-inverse.json',D/'baseline-tree.json',Path(__file__)]
result=dict(accepted=True,findings=[],reviewer='independent production reviewer',passed=186622,total=186622,expected_failures=0,errors=0,broken=0,skipped=0,ordinary_files=34,inventory_entries=1221,elapsed_shared_seconds=done['elapsed_shared_seconds'],minimum_available_kib=minimum,maximum_swap_kib=maximum,child_maxrss_kib=p['child_maxrss_kib'] if isinstance(p,dict) else read(Q/'output/process.json')['child_maxrss_kib'],review=str(Q/'RESULT-REVIEW.md'),bindings={str(f):sha(f) for f in files})
put(Q/'result-review.json',result);print(json.dumps({k:v for k,v in result.items() if k!='bindings'}));print('SHA256',sha(Q/'result-review.json'))
