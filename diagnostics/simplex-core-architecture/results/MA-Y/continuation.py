from pathlib import Path
import json,hashlib,subprocess,time
D=Path(__file__).resolve().parent;R=D.parents[3];X=D.with_name('MA-X')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text())
rev=rd(D/'result-review.json');h=rd(D/'host.json');groups=rd(D/'posthost.json')['groups']
if rev['accepted'] is not True or rev['qualification_accepted'] is not False or rev['findings'] or not all(sha(p)==v for p,v in rev['sha256'].items()):raise SystemExit('review not accepted/bound')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'exe').resolve().name.startswith('julia'):matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
refs={k:subprocess.check_output(['git',*a],cwd=R,text=True).strip() for k,a in {'head':['rev-parse','HEAD'],'master':['rev-parse','master'],'branch':['branch','--show-current'],'remote':['ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture']}.items()}
if matches or boot!=h['boot_id'] or refs!=h['refs']:raise SystemExit('fresh host/ref')
status=R/'diagnostics/simplex-core-architecture/STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
for p,q in [(status,D/'STATUS.md.before-MA-Y'),(road,D/'roadmap.md.before-MA-Y')]:
 if p.read_bytes()!=q.read_bytes():raise SystemExit('continuation drift')
body='''MA-Y completed: complete MA-U DenseLU candidate qualification NOT ACCEPTED.
See MA-DENSELU-COMPLETE-QUALIFICATION.md and MA-Y/result-review.md/json.
Fresh numerical seal accepted46checks/40bindings before exactly ONE sequence.
Three serial exit0 Julia processes17.831977054/11.766976578/11.808823572seconds,
total41.407777204seconds. Smoke16/16, originalqualification4329/4329 and exact
0pass/2expectedmissing-routeTest.Fail/0error RED. All160correctness and52cost cases
perprocess complete;12480costcalls/3120windows/2184measured/936warm. Every measured
compile/recompile0; all28GCwindows retained; every output/owner check passes.

Processes1/2 passed all52cost gates. Process3 fails scopedBigFloatBTRAN side-time
351.15us versus299.575us (delta51.575us exceeds29.9575us) and RationalFTRAN median
bytes3247408 versus3247376 (+32bytes per4callwindow; equal74525events). All36target
cases pass perprocess pairedratio/bytes/events gates; local ratios.536057–.816072
are not complete pooled acceptance or publicsolver speedup. Pairedratio cannot
replace control side-time rule. No allocator/timing cause established.
Launcherexit1/audit-3 false preserved. NOaggregate run after failedstage; no retry,
tuning, filtering, bytewaiver, baselinecorrection or productionpromotion.

This allowance is CONSUMED. MA-X driver/launcher/auditors, allnewraw/journals/pins/
reviews and MA-Y checks are FROZEN NEVER RERUN/rewrite. Do not execute the older
MA-X next-MA-Y instruction below again. MA-S-2 rejected48/52 and narrowerMA-V
acceptance remain unchanged. Both controls failed, not Rationalalone. No immediate
allocator investigation or automatic unchanged-candidate retry is authorized.
OriginalTask3 compatibility/dependency/clean-loading/PFI/publicafiro/sc50a work
is NOT opened by this rejection. A genuinely different proposal needs its own
concrete evidence-based plan/admission. Broader performance plan stays OPEN;
other independently authorized work must still respect its own gates.

Postcheck16integrity/cleanup/stop gates pass separately from failedcostacceptance.
All4375pins/source514/protected6 unchanged. Full176historical+newgroups ORsessions
absent, noJulia. Before future numerical work or continuation edits require NEW
refs/boot/start_ticks/command/fullgroups/sessions, not reuse MA-Y/posthost.json.
Six MA-X current closure/publication/continuation STATUS/roadmap bindings map ONLY
to MA-Y beforecopies; alloldermaps preserved. No production/test/env/CI/master
change; master6f68e24, CIoff, HHdisabled, automationpaused unchanged.
'''
s=status.read_text();marker='## Exact next action\n\n'
if s.count(marker)!=1:raise SystemExit('status marker')
s=s.replace(marker,marker+body+'\n## Previous MA-X preparation (completed; allowance now consumed)\n\n',1)
status.write_text(s);road.write_text(road.read_text().rstrip()+'\n\n## MA-Y complete DenseLU qualification rejected (2026-10-14)\n\n'+body)
checks=dict(review=rev['accepted'] is True and rev['qualification_accepted'] is False,host=not matches and refs==h['refs'] and len(groups)==176,before_exact=all(sha(m['preserved'])==m['sha256']==rd(m['source'])['sha256'][m['path']] for m in rd(D/'continuation-map.json')['old_bindings']),source514=all(sha(R/p)==v for p,v in h['master_identity'].items()),protected6=all(sha(p)==v for p,v in h['protected'].items()))
with (D/'continuation.json').open('x') as f:json.dump(dict(all_passed=all(checks.values()),checks=checks,host=dict(time=time.time(),boot_id=boot,groups=groups,matches=matches,refs=refs),sha256={str(p):sha(p) for p in [D/'continuation.py',D/'continuation-map.json',status,road]}),f,indent=2);f.write('\n')
if not all(checks.values()):raise SystemExit(1)
print('continuation PASS; six X binding maps preserved; qualification remains rejected')
