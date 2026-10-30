from pathlib import Path
import json,hashlib,subprocess
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');M=Path('/home/jspitz/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-task3/2026-10-30';P=W/'diagnostics/dual-recovery-devex-task2/2026-10-30';L=W/'.superpowers/sdd/2026-10-30-dual-recovery-devex-fallback/progress.md'
def git(repo,*a):return subprocess.check_output(['git','-C',str(repo),*a],text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if D.exists():raise RuntimeError('fresh directory required')
if git(W,'rev-parse','--git-dir')==git(W,'rev-parse','--git-common-dir') or git(W,'rev-parse','--show-superproject-working-tree'):raise RuntimeError('linked worktree required')
old=json.loads((P/'host.json').read_text());boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();groups=set(old['checked_groups']);conflicts=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  stat=(p/'stat').read_text();a=stat[stat.rfind(')')+2:].split();pgid,sid,start=int(a[2]),int(a[3]),int(a[19]);comm=(p/'comm').read_text().strip()
  if comm.lower().startswith('julia') or (boot==old['boot_id'] and (pgid in groups or sid in groups)):
   conflicts.append(dict(pid=int(p.name),pgid=pgid,sid=sid,start_ticks=start,boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except(FileNotFoundError,ProcessLookupError):pass
if conflicts:raise RuntimeError(conflicts)
refs={str(r):{v:git(r,'rev-parse',v) for v in ('HEAD','master','origin/master')} for r in (W,M)}
if refs[str(W)]['HEAD']!='1509f43f9a288bfa5b3ae004e0e9f07b560b5469':raise RuntimeError(refs)
if any(v!='c0fa748ffa61ccb7c1caaf248c40324f60bc737b' for r,values in refs.items() for k,v in values.items() if not(r==str(W) and k=='HEAD')):raise RuntimeError(refs)
if git(W,'diff','--name-only','HEAD') or git(W,'diff','--cached','--name-only'):raise RuntimeError('tracked/index changes')
D.mkdir(parents=True)
(D/'host.json').write_text(json.dumps(dict(boot_id=boot,previous_boot_id=old['boot_id'],checked_groups=sorted(groups),conflicts=conflicts,refs=refs,scope='fresh source preparation preflight, not runtime admission'),indent=2)+'\n')
paths=[W/'AGENTS.md',W/'docs/superpowers/plans/2026-10-30-dual-recovery-devex-fallback.md',W/'docs/superpowers/specs/2026-10-30-dual-recovery-devex-fallback-design.md',P/'simplex_numerics.jl',P/'simplex_recovery.jl',P/'recovery_weight_tests.jl',P/'REVIEW-FINAL.md',P/'review-final.json',P/'closure.json',P/'publication.json']
paths+=list((W/'src').rglob('*.jl'))
for p in (W/'src').rglob('*.jl'):
 if p.read_bytes()!=(M/p.relative_to(W)).read_bytes():raise RuntimeError(p)
(D/'source-pins.json').write_text(json.dumps(dict(bindings={str(p):sha(p) for p in paths},production_equal_master=71,scope='readtime source preparation, not launch pins'),indent=2)+'\n')
(D/'progress.md.before-Task3').write_bytes(L.read_bytes())
with L.open('a') as f:f.write('\nTask3 source preparation started from1509f43f. Existing isolated worktree reused. Ruling: explicit user no-Julia scope overrides baseline tests, runtime TDD/task-done and cleanup. Write prospective tests first; actual src/test/env/CI/master unchanged; isolated Task3 constructor/publication only; Task4 not admitted. Fresh727 groups AND sessions/noJulia/refs preflight; no old scripts rerun.\n')
print(json.dumps(dict(directory=str(D),groups=len(groups),boot=boot,source_pins=len(paths),refs=refs)))
