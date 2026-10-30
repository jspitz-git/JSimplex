from pathlib import Path
import json,subprocess,hashlib
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-plan/2026-10-30';M=Path('/home/jspitz/JSimplex.jl')
if D.exists():raise RuntimeError('fresh record required')
D.mkdir(parents=True)
old=json.loads((W/'diagnostics/dual-weight-validity-contract/2026-10-30/host.json').read_text());boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();groups=set(old['checked_groups']) if boot==old['boot_id'] else set();conflicts=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  stat=(p/'stat').read_text();a=stat[stat.rfind(')')+2:].split();pgid,sid,start=int(a[2]),int(a[3]),int(a[19]);comm=(p/'comm').read_text().strip()
  if comm.lower().startswith('julia') or pgid in groups or sid in groups:conflicts.append(dict(pid=int(p.name),pgid=pgid,sid=sid,start_ticks=start,boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except(FileNotFoundError,ProcessLookupError):pass
if conflicts:raise RuntimeError(conflicts)
refs={str(repo):{r:subprocess.check_output(['git','-C',str(repo),'rev-parse',r],text=True).strip() for r in ['HEAD','master','origin/master']} for repo in [W,M]}
if refs[str(W)]['HEAD']!='028b3efc8a60c880ddb863fb08537d0c8cc1ece1':raise RuntimeError(refs)
if any(v!='c0fa748ffa61ccb7c1caaf248c40324f60bc737b' for k,rows in refs.items() for r,v in rows.items() if not(k==str(W) and r=='HEAD')):raise RuntimeError(refs)
(D/'host.json').write_text(json.dumps(dict(boot_id=boot,checked_groups=sorted(groups),conflicts=conflicts,refs=refs),indent=2)+'\n')
files=['AGENTS.md','src/simplex_recovery.jl','src/simplex_numerics.jl','src/simplex_pivot.jl','src/simplex_pricing.jl','src/simplex_driver.jl','src/simplex_precision.jl','src/simplex.jl','src/dual_simplex.jl','src/simplex_diagnostics.jl','test/basis_recovery_tests.jl','test/dual_simplex_tests.jl','test/dual_weight_validation_tests.jl','test/adaptive_pricing_lifecycle_tests.jl','test/partial_pricing_edge_tests.jl','test/runtests.jl','diagnostics/dual-weight-validity-contract/2026-10-30/REPORT.md','diagnostics/dual-weight-validity-contract/2026-10-30/REVIEW-FINAL.md','diagnostics/klu-weight-rejection/2026-10-29/REPORT.md','diagnostics/klu-homogeneous-cleanup/2026-10-30/REPORT.md']
bindings={str(W/p):hashlib.sha256((W/p).read_bytes()).hexdigest() for p in files};n=0
for p in (W/'src').rglob('*.jl'):
 if p.read_bytes()!=(M/p.relative_to(W)).read_bytes():raise RuntimeError(p)
 n+=1
(D/'source-pins.json').write_text(json.dumps(dict(scope='readtime plan inputs, not runtime launch pins',bindings=bindings,production_files_equal_master=n),indent=2)+'\n');print(json.dumps({'groups':len(groups),'conflicts':conflicts,'readtime_bindings':len(bindings),'production_equal_master':n}))
