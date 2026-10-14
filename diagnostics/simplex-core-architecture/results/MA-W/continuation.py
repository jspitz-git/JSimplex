from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-W';h=json.loads((D/'host.json').read_text());rev=json.loads((D/'review.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
if not(rev['accepted'] is True and rev['findings']==[] and all(sha(p)==v for p,v in rev['sha256'].items())):raise SystemExit('review')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(f[2]) in h['groups'] or int(f[3]) in h['groups'] or (p/'exe').resolve().name.startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
refs={k:subprocess.check_output(['git',*a],text=True).strip() for k,a in {'head':['rev-parse','HEAD'],'master':['rev-parse','master'],'branch':['branch','--show-current'],'remote':['ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture']}.items()}
if matches or refs!=h['refs'] or boot!=h['boot_id']:raise SystemExit('fresh host')
maps=json.loads((D/'continuation-map.json').read_text())['old_bindings']
if not all(sha(m['path'])==sha(m['preserved'])==m['sha256'] for m in maps):raise SystemExit('beforecopies')
block='''MA-W complete-candidate qualification design accepted, SOURCE/DESIGN ONLY.
See docs/superpowers/plans/2026-10-14-ma-denselu-complete-qualification.md and
MA-W/review.md/json. Exact unchanged MA-U candidate; original52cost cases and
strict MA-S-2 paired-ratio target/side-median control reducers, no Rational waiver.
No new candidate/driver/launcher/Julia/parser/import/compile/numerics in MA-W.

Next concrete step MA-X: prepare NEW complete immutable offline admission/driver,
using MA-S-LOAD corrected cold dispatch boundaries, MA-U candidate/instrumented,
MA-R reference/tests/fixtures. Add partial-record preservation and strict per-process
cost refusal before any next process. Freeze exact commands, schema, source/runtime/
environment hashes and independent admission review BEFORE a future numerical seal.
Future MA-Y at most3serial processes90s each/270total, one attempt, no retry/tuning;
standing human short-run permission persists, no repeated permission question.

Prospective complete budget:160correctness cases/488direct smoke+correctness entries,
12,480cost entries/3,120windows/2,184measured/936warm,318setup factorizations including
2PFI constructors and2PFI copies; nested/backend/import work additional. Reuse MA-V
mode/owner coverage only by exact source identity; no duplicate840case/micro run.
All52 must pass. Rational bytes/events strict no-increase per process; time budgets
unchanged. Any failed process gate stops later processes. No causal allocation claim
from equal events or even a future PASS. If Rational alone fails, stop the unchanged
full-candidate route; no automatic repeat or allocator investigation.

MA-S-2 stays rejected48/52. MA-V local guard acceptance remains separate; its sequence
is consumed and all evidence frozen. Component PASS would still require separate
production compatibility/dependency/PFI/public afiro-sc50a admission before integration.
All old frozen scripts/raw/reviews remain untouched; no automatic old52case rerun.
Six V-EXEC current closure/publication/continuation STATUS/roadmap bindings map ONLY
to MA-W beforecopies through continuation-map.json; all older mappings preserved.
Before real new work refresh refs/boot/start_ticks/command/full170groups ANDsessions/
noJulia; stale MA-W host is not a fresh preflight. Master6f68e24/source514/protected6
unchanged; CIoff/HHdisabled/automationpaused; broader performance plan OPEN.
'''
p=R/'diagnostics/simplex-core-architecture/STATUS.md';s=p.read_text();a=s.index('## Exact next action\n');b=s.index('## Previous MA-S admission preparation',a);old=s[a+len('## Exact next action\n'):b].strip();p.write_text(s[:a]+'## Exact next action\n\n'+block+'\n## Previous MA-V qualification (completed)\n\n'+old+'\n\n'+s[b:])
q=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';s=q.read_text();q.write_text(s.rstrip()+'\n\n## MA-W complete-candidate qualification design (2026-10-14)\n\n'+block)
o=dict(all_passed=True,host=dict(time=time.time(),refs=refs,boot_id=boot,groups=h['groups'],matches=matches),sha256={str(x):sha(x) for x in [p,q,D/'continuation.py',D/'review.json',D/'continuation-map.json']})
with (D/'continuation.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print('Updated continuation after accepted review and fresh170group host check')
