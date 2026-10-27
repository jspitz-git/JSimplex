from pathlib import Path
import json,hashlib,subprocess,os,datetime,ast,tomllib
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-local/2026-10-27');Q=D/'RED-run';S=D/'RED';M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2];O=R/'diagnostics/generic-quality-devex/2026-10-27';base='ca64312f7f74b1d7bec047718399f229674b3e1d'
def need(v,m):
 if not v:raise RuntimeError(m)
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
def git(*a):return subprocess.check_output(['git','-C',str(M),*a],env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')).decode().strip()
pins=read(Q/'pins.json');need(len(pins['inventory'])==1226,'inventory count')
for n,v in pins['inventory'].items():p=Path(n);need(str(p.resolve(strict=True))==v['resolved'] and sha(p)==v['sha256'],'pin '+n)
for tree in pins['trees']:need({str(p) for p in Path(tree).rglob('*') if p.is_file()}=={n for n in pins['inventory'] if Path(n).is_relative_to(tree)},'membership '+tree)
basefiles=read(D/'baseline-tree.json');actual={str(p.relative_to(S)):sha(p) for p in S.rglob('*') if p.is_file()}
need(sorted(n for n in basefiles.keys()|actual.keys() if basefiles.get(n)!=actual.get(n))==['test/generic_quality_local_tests.jl','test/runtests.jl'],'RED only tests change')
for n,h in basefiles.items():
 need(sha(D/'baseline'/n)==sha(M/n)==h,'authoritative base '+n)
 if n!='test/runtests.jl':need(sha(S/n)==h,'RED original bytes '+n)
need((S/'test/runtests.jl').read_text()==(D/'baseline/test/runtests.jl').read_text()+'\ninclude("generic_quality_local_tests.jl")\n','ordinary include only')
need(sha(D/'new-test-draft.jl')==sha(D/'new-test.jl')==sha(S/'test/generic_quality_local_tests.jl')=='12c0b1a8d0be69095f9588fa3057ee0d86b31bf0efbb0e8f11492898aaf139ce','frozen precost draft')
test=(D/'new-test.jl').read_text();need((D/'comparison-2/Reference.jl').read_text() in test and (D/'comparison-2/fixtures.jl').read_text() in test,'exact reference/fixtures')
need(all('const Local'+n+'=JSimplex' in test for n in ['CandidateA','CandidateB','CandidateAB','CandidateC']),'actual package candidates')
for ref in ['HEAD','master','origin/master']:need(git('rev-parse',ref)==base,'base refs')
need(not git('diff','--name-only','HEAD','--','src','test','Project.toml'),'production untouched')
for group in read(Q/'protected-before.json').values():
 for n,h in group.items():need(sha(Path(n))==h,'protected '+n)
r=read(D/'comparison-2/result-review.json');need(r['accepted'] and r['findings']==[],'measurement accepted')
for n,h in r['bindings'].items():need(sha(Path(n))==h,'comparison review binding '+n)
# Independently verify the preregistered permanent cost cells against all nine original measurement pairs.
cells=tomllib.loads((D/'comparison-2/output/results.toml').read_text())['cells'];gates=[]
for scope,pattern,rows,variant in [('quality','negative',0,'AB'),('quality_transposed','negative',0,'AB'),('finish','mixed',0,'B'),('audit','positive',4,'C')]:
 matches=[c for c in cells if c['context']=='BF128_RoundingMode{:Nearest}()' and c['n']==96 and c['scope']==scope and c['pattern']==pattern and c['basis_rows']==rows and c['variant']==variant and c['density']==('vector' if scope=='finish' else 'dense')];need(len(matches)==1,'preregistered gate '+scope);cell=matches[0];ratios=[]
 for pair in range(1,10):
  old=next(w for w in cell['windows'] if w['pair']==pair and w['arm']=='original');new=next(w for w in cell['windows'] if w['pair']==pair and w['arm']==variant);need(new['bytes']<old['bytes'] and new['events']<old['events'],'all nine lower '+scope);ratios.append([new['bytes']/old['bytes'],new['events']/old['events']])
 gates.append(dict(id=cell['id'],maximum_bytes_ratio=max(v[0] for v in ratios),maximum_events_ratio=max(v[1] for v in ratios)))
c=read(Q/'contract.json');need(c['arm']=='RED' and c['files']==['generic_quality_local_tests.jl'] and c['source_root']==str(S) and c['attempts']==1 and c['expected_failures']==4 and c['expected_exit']==1 and c['shared_limit_seconds']==2400 and c['guard_limit_seconds']==2392,'concrete RED contract')
need(c['expected_failure_locations']==[[str(S/'test/generic_quality_local_tests.jl'),440]]*4 and '# RED whole-call cost gate' in test.splitlines()[439],'exact cost location')
for n in ['entry_gate.py','guard_reviewed.py','supervisor_reviewed.py']:need((Q/'guard'/n).read_bytes()==(O/'MASTER-run/guard'/n).read_bytes(),'reviewed guards unchanged')
need((Q/'launch.py').read_bytes()==(O/'MASTER-run/launch.py').read_bytes(),'reviewed2400 launch')
need((Q/'audit.py').read_text()==(O/'MASTER-run/audit.py').read_text().replace('QUALITY_DEVEX','LOCAL_QUALITY').replace('Quality Devex ','Local quality '),'reviewed auditor only labels')
for n in ['launch.py','audit.py','common.py','prepare.py']:ast.parse((Q/n).read_text())
need((Q/'common.py').read_bytes()==(D/'common_next.py').read_bytes(),'exact refined common')
old=(D/'common.py').read_text();new=(D/'common_next.py').read_text();prefix="   need(pgid not in groups and sid not in groups,'historical group/session');";i=new.index('   if pgid in groups or sid in groups:');j=new.index("   need(not any(Path(v).name.lower().startswith('julia')",i)
need(new[:i]+prefix+new[j+3:]==old,'only exact identity refinement')
allow=read(D/'host-identity-allowance.json');need(sha(D/'host-identity-allowance.json')=='f0b6a5093b9c1875ec8718bca8775bc44ba4d6d6ab98a1ac23adfe52d69f2a92','fixed allowance');hist=Path(allow['historical_record']);need(sha(hist)==allow['historical_sha256'] and read(hist)['child']==allow['historical_child'],'actual archived child')
need(len(allow['identities'])==1,'single exemption');permitted=allow['identities'][0];need(permitted['pid']==permitted['pgid']==permitted['sid']==77336 and permitted['command']==['/usr/libexec/wsl-pro-service'] and permitted['start_ticks']==6151792 and permitted['boot_id']!=allow['historical_child']['boot_id'],'unrelated full tuple')
seed=read(Q/'host-seed.json');need(seed==read(D/'comparison-2/audit-host.json'),'historical continuity');groups=set(seed['groups']);boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==seed['boot_id']==permitted['boot_id'],'same current boot');processes=[];collisions=[]
for proc in Path('/proc').glob('[0-9]*'):
 try:
  st=(proc/'stat').read_text().rsplit(')',1)[1].split();args=[x.decode(errors='replace') for x in (proc/'cmdline').read_bytes().split(b'\0') if x];comm=(proc/'comm').read_text().strip();a=dict(pid=int(proc.name),pgid=int(st[2]),sid=int(st[3]),start_ticks=int(st[19]),command=args,boot_id=boot)
  if a['pgid'] in groups or a['sid'] in groups:need(a==permitted,'unexpected historical collision');collisions.append(a)
  need(not any(Path(v).name.lower().startswith('julia') for v in [comm]+args[:1]),'Julia active');processes.append(a)
 except (FileNotFoundError,ProcessLookupError):pass
need(collisions==[permitted],'current exact service collision')
mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'fresh memory')
need(not (Q/'output').exists() and not (Q/'reservation.json').exists(),'exclusive not launched')
put(Q/'independent-admission-host.json',dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=processes,no_Julia=True,verified_unrelated_collisions=collisions,historical_numerical_identities_absent=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']))
report='''Verdict: RED ADMITTED for one guarded 2400-second attempt (2392-second inner cutoff), expecting exactly four whole-call allocation failures and no correctness errors, broken tests or skips. No unresolved findings. This admission does not accept a production change or a future failed GREEN/master gate.

All 1226 inventory entries were independently SHA256-streamed with resolved-path and complete-tree membership checks. All 535 baseline files equal authoritative ca64312f7f74b1d7bec047718399f229674b3e1d. RED retains every source and prior test byte; only the exact preregistered new test and appended ordinary include differ. Draft/new/installed test hash is 12c0b1a8d0be69095f9588fa3057ee0d86b31bf0efbb0e8f11492898aaf139ce, unchanged since before comparison cost data. The exact comparison reference and fixtures are embedded and all candidates alias actual JSimplex. Four fixed warmed alternating whole-call gates require lower bytes AND events, without time assertions or selected reruns. Each gate is independently supported by all nine corresponding measurement pairs; this is separate from witnessing baseline RED. Expected failures are only the four executions of line440. Existing thresholds remain unchanged.

The corrected comparison's independent acceptance and all its bindings were revalidated. A/B/C and AB acceptance rests on whole-call allocation/work evidence, with timing regressions and generic scalar-roundoff dispatch scope preserved in WORK-MEMORY.md and the comparison report. No new production scan, solve, copy, conversion or retained cache is proposed. Generic bodies, numerical/owner/precision checks remain. New custom-matrix, finalizer invalid-scale/large-term and hardware-result/BigFloat-work tests are ordinary correctness controls, not removed safeguards.

The process preflight refinement is accepted as exact identity disambiguation. The archived numerical child77336 is independently verified by its original process.json hash, boot4fde10f2 and start3810211. Current numeric group/session77336 is occupied by /usr/libexec/wsl-pro-service with boot781795f4, PID/PGID/SID77336 and start6151792. The allowance fixes the full boot/PID/PGID/SID/start/command tuple under a hardcoded SHA256. Any changed tuple or additional occupant is rejected; the Julia-process check still applies outside the allowance. Independent text comparison shows this is the sole common-helper change. No historical group number is removed and no service is killed. Fresh evidence checks all historical groups AND sessions: historical numerical identities are absent; literal numeric77336 is present solely as this unrelated different-boot service. The two refused offline preparations and partial configuration remain preserved, and neither was a Julia run.

Guard/entry/supervisor and2400-second launch match the previously reviewed runtime. Auditor differs only in task labels and requires exact failure locations/ordinary Test schema. Package/project identity, Julia/BLAS1, GC1,0, heap2GiB, AS8GiB, RAMavailable6GiB/swap1GiB, entry/parent-death/owned cleanup, exclusive attempt and inclusive budget checks remain. Fresh independent host records no live Julia and adequate resources, with protected files/indexes and master refs unchanged. The launcher must refresh all bindings and host checks before executing. Reviewer launched no Julia and mutated no source/index/ref.
'''
with (Q/'ADMISSION-REVIEW.md').open('x') as f:f.write(report)
files=[Path(n) for n in pins['inventory']]+[p for p in Q.rglob('*') if p.is_file()]+[D/n for n in ['HOST-IDENTITY.md','host-identity-allowance.json','common_next.py','preflight-refusal.json','comparison-2/result-review.json','comparison-2/RESULT-REVIEW.md','WORK-MEMORY.md','independent-red-admission-check.py']]+[hist]
put(Q/'admission.json',dict(accepted=True,findings=[],attempts=1,expected_failures=4,review=str(Q/'ADMISSION-REVIEW.md'),gate_measurement_support=gates,bindings={str(p):sha(p) for p in files}))
print(json.dumps(dict(accepted=True,pins=len(pins['inventory']),historical_groups=len(groups),unrelated_numeric_collision=77336,sha256=sha(Q/'admission.json'),gate_support=gates)))
