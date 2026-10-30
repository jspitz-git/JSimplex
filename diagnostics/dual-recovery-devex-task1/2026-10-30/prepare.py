from pathlib import Path
import json,subprocess,hashlib
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');M=Path('/home/jspitz/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-task1/2026-10-30';L=W/'.superpowers/sdd/2026-10-30-dual-recovery-devex-fallback/progress.md'
if D.exists():raise RuntimeError('fresh preparation required')
if L.exists():raise RuntimeError('existing plan ledger must be resumed explicitly')
D.mkdir(parents=True)
old=json.loads((W/'diagnostics/dual-recovery-devex-plan/2026-10-30/host.json').read_text());boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();groups=set(old['checked_groups']) if boot==old['boot_id'] else set();conflicts=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  stat=(p/'stat').read_text();a=stat[stat.rfind(')')+2:].split();pgid,sid,start=int(a[2]),int(a[3]),int(a[19]);comm=(p/'comm').read_text().strip()
  if comm.lower().startswith('julia') or pgid in groups or sid in groups:conflicts.append(dict(pid=int(p.name),pgid=pgid,sid=sid,start_ticks=start,boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except(FileNotFoundError,ProcessLookupError):pass
if conflicts:raise RuntimeError(conflicts)
refs={str(repo):{r:subprocess.check_output(['git','-C',str(repo),'rev-parse',r],text=True).strip() for r in ['HEAD','master','origin/master']} for repo in [W,M]}
if refs[str(W)]['HEAD']!='24a79f0babfba545387bad65939b5d1b51767f56':raise RuntimeError(refs)
if any(v!='c0fa748ffa61ccb7c1caaf248c40324f60bc737b' for k,rows in refs.items() for r,v in rows.items() if not(k==str(W) and r=='HEAD')):raise RuntimeError(refs)
(D/'host.json').write_text(json.dumps(dict(boot_id=boot,checked_groups=sorted(groups),conflicts=conflicts,refs=refs),indent=2)+'\n')
paths=['AGENTS.md','src/simplex_numerics.jl','src/simplex_recovery.jl','src/simplex_pivot.jl','src/simplex.jl','src/refactorization_policy.jl','src/simplex_diagnostics.jl','docs/superpowers/plans/2026-10-30-dual-recovery-devex-fallback.md','docs/superpowers/specs/2026-10-30-dual-recovery-devex-fallback-design.md','diagnostics/dual-recovery-devex-plan/2026-10-30/REVIEW-FINAL.md']
bindings={str(W/p):hashlib.sha256((W/p).read_bytes()).hexdigest() for p in paths};n=0
for p in (W/'src').rglob('*.jl'):
 if p.read_bytes()!=(M/p.relative_to(W)).read_bytes():raise RuntimeError(p)
 n+=1
(D/'source-pins.json').write_text(json.dumps(dict(bindings=bindings,production_equal_master=n,scope='offline preparation readtime sources, not runtime launch pins'),indent=2)+'\n')
L.write_text('# SDD ledger — plan: docs/superpowers/plans/2026-10-30-dual-recovery-devex-fallback.md\n\nTask1: preparation in progress; baseline24a79f0b, production c0fa748f.\nPre-flight: Task1 outcome quality/cause/invalid_seen feeds Task2 weight classification; Task2 fixed result feeds Task3 cold publication. Names and default strict behavior checked against final spec/plan.\nRuling: this turn prepares only the explicitly proposed next Task1 candidate/tests and its source review. Tasks2–4 remain pending.\nRuling: accepted Global Constraints override generic skill runtime/TDD/task-done commands: no Julia query/parser/import/compile or RED/GREEN now. Write prospective tests first; keep all runtime assertions UNEXECUTED until concrete Task4 admission. Do not run baseline tests, install dependencies or alter actual src/test/env.\nRuling: existing attached native-quality-scans linked worktree is reused; no new worktree or cleanup.\n')
print(json.dumps({'groups':len(groups),'conflicts':conflicts,'source_pins':len(bindings),'production_equal_master':n,'directory':str(D),'ledger':str(L)}))
