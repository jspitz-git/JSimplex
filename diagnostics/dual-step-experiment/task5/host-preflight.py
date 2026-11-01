from pathlib import Path
import sys,json,importlib.util
sys.dont_write_bytecode=True
W=Path('/home/jspitz/.codex/worktrees/dual-step-experiment/JSimplex.jl');D=W/'diagnostics/dual-step-experiment/task4'
s=importlib.util.spec_from_file_location('task4hostdefinitions',D/'run2.py');L=importlib.util.module_from_spec(s);s.loader.exec_module(L)
h=L.H.host(L.O/'run-1');groups=set(json.loads((D/'closure-host.json').read_text())['checked_groups'])|set(h['checked_groups'])
for p in Path('/proc').glob('[0-9]*'):
 try:
  a=L.H.H.identity(p.name)
  if a['pgid'] in groups or a['sid'] in groups:raise ValueError('historical group/session active')
 except (FileNotFoundError,ProcessLookupError):pass
head=L.H.H.git(W,'rev-parse','HEAD')
if head!='8e31807121f4e709fcfca0d9ba379aa0a2199d8c':raise ValueError('HEAD changed')
if L.H.H.git(W,'branch','--show-current')!='codex/dual-step-experiment':raise ValueError('branch')
if L.H.H.git(W,'status','--porcelain'):raise ValueError('dirty worktree')
h.update(checked_groups=sorted(groups),experiment=head,no_julia=True)
with Path('/tmp/task5-host.json').open('x') as f:json.dump(h,f,indent=2)
print(json.dumps(dict(head=head,boot=h['boot_id'],groups_and_sessions=len(groups),no_julia=True,conflicts=h['conflicts'])))
