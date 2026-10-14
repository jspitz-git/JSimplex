from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';E=D/'results/MA-V-EXEC';h=json.loads((E/'posthost.json').read_text());m=json.loads((E/'continuation-map.json').read_text())['old_bindings'];review=json.loads((E/'reviewer-check.json').read_text());boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,o):
 with p.open('x') as f:json.dump(o,f,indent=2);f.write('\n')
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(s[2]) in h['groups'] or int(s[3]) in h['groups'] or (p/'exe').resolve().name.startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(s[2]),sid=int(s[3]),start_ticks=int(s[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
refs={k:subprocess.check_output(['git',*a],text=True).strip() for k,a in {'head':['rev-parse','HEAD'],'master':['rev-parse','master'],'branch':['branch','--show-current'],'remote':['ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture']}.items()}
if matches or boot!=h['boot_id'] or refs!=h['refs']:raise SystemExit('fresh host failure')
save(E/'continuation-host.json',dict(time=time.time(),boot_id=boot,groups=h['groups'],matches=matches,refs=refs))
paths={x['path']:x['preserved'] for x in m};rm=[]
for p,q in paths.items():
 if sha(p)!=sha(q) or sha(q)!=review['sha256'][p]:raise SystemExit('beforecopy binding')
 rm.append(dict(source=str(E/'reviewer-check.json'),path=p,preserved=q,sha256=sha(q),kind='sha256'))
save(E/'reviewer-continuation-map.json',dict(old_bindings=rm,scope='Only current continuation bindings inherited into independent reviewer-check; original eight mappings and all older mappings unchanged'))
block='''MA-V short qualification completed: the isolated MA-U guard passes MA-T Task2
local numerical/cost gates. Exactly one sequence, two processes26.838440328s and
9.809628626s supervised (36.648068954s total), both exit0; no retry. Correctness
25,861/25,861 assertions,270predicate records/25transitions/840whole cases,
844direct calls per arm. Actual dedicated no-scope case unavailable; source proof
only for that branch. Both old-guard RED cases +128bytes/+8events per4-call window.
All12 per-process and pooled whole-cost gates pass; new micro helper zero allocation
in all six contexts. All eight fallback/n15 controls have identical allocation
medians to reference; four eligible n32 cases show local whole-call C/R0.617–0.686,
including existing MA arithmetic, not isolated guard savings or fullsolver speedup.
All measured compile/recompile0; three measured GC windows retained. Exact2,080cost
entries/61,440micro/2,532directcorrectness entries; nested work separately counted.
Stage audits23each; aggregate12/12; freshpostcheck20/full4,342pins/source514/protected6.
Independent result review and report: MA-ROUNDING-GUARD-QUALIFICATION.md and
MA-V-EXEC/result-review.md/json. Probe LLVM delegates to helper;749byte probe text
is not transitive helper/native code size. Original report wording preserved.

MA-V sequence allowance CONSUMED; all V/EXEC scripts/raw/pins/audits/reviews freeze
at publication. Do not rerun launcher, auditor, numerical tests or old collectors.
MA-S-2 remains rejected48/52; Rational no-increase controls and complete-candidate
obligations remain OPEN. Next is a separately reviewed complete-candidate admission
addressing all remaining controls using preserved evidence. No automatic old52case
rerun, tuning, production promotion or master integration. Standing human short-run
permission persists; new concrete immutable admission remains mandatory.

Eight V current STATUS/roadmap bindings (pins/preparation review/closure/publication)
map ONLY to MA-V-EXEC before-MA-V-execution copies via continuation-map.json.
Two inherited reviewer-check continuation bindings use reviewer-continuation-map.json;
all older mappings remain. Numerical seal binds preserved copies. Fresh full170groups
ANDsessions/noJulia checked before continuation edits; actual process identities in
V/run-1 and run-2/process.json and EXEC/posthost.json. Next real work needs fresh
host refs/boot/start_ticks/command/full170groups ANDsessions, not stale host reuse.
Master6f68e24/source/test/userenv unchanged; CIoff/HHdisabled/automationpaused.
Broader S2/S3/S4/S5/S6 and MA performance plan remain OPEN.
'''
p=D/'STATUS.md';s=p.read_text();a=s.index('## Exact next action\n');b=s.index('## Previous MA-S admission preparation',a);p.write_text(s[:a]+'## Exact next action\n\n'+block+'\n'+s[b:])
p=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';s=p.read_text();p.write_text(s.rstrip()+'\n\n## MA-V rounding guard short qualification (2026-10-14)\n\nThis completed result supersedes the preceding MA-V unexecuted next-action text.\n\n'+block)
save(E/'continuation.json',dict(checks=dict(fresh_host=not matches and refs==h['refs'],eight_original_maps=len(m)==8,two_reviewer_maps=len(rm)==2),sha256={str(p):sha(p) for p in [E/'continuation.py',E/'continuation-host.json',E/'reviewer-continuation-map.json',D/'STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']}))
print('Continuation updated; 8 original + 2 reviewer maps preserved; fresh170groups clear')
