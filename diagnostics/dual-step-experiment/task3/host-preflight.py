from pathlib import Path
import importlib.util,sys,json
sys.dont_write_bytecode=True
W=Path('/home/jspitz/.codex/worktrees/dual-step-experiment/JSimplex.jl');old=W/'diagnostics/dual-step-experiment/task2'
s=importlib.util.spec_from_file_location('task2defs',old/'run.py');L=importlib.util.module_from_spec(s);s.loader.exec_module(L)
h=L.H.host(L.O/'run-1');groups=set(json.loads((old/'closure-host.json').read_text())['checked_groups'])|set(h['checked_groups'])
for p in Path('/proc').glob('[0-9]*'):
 try:
  a=L.H.H.identity(p.name)
  if a['pgid'] in groups or a['sid'] in groups:raise ValueError('old group/session active')
 except (FileNotFoundError,ProcessLookupError):pass
head=L.H.H.git(W,'rev-parse','HEAD')
if head!='b2d74da078d5e8361fccaa4fc74e9f6abb750548':raise ValueError('unexpected HEAD')
if L.H.H.git(W,'branch','--show-current')!='codex/dual-step-experiment':raise ValueError('wrong branch')
if L.H.H.git(W,'status','--porcelain'):raise ValueError('worktree not clean')
h.update(checked_groups=sorted(groups),experiment=head,no_julia=True)
with Path('/tmp/task3-host.json').open('x') as f:json.dump(h,f,indent=2)
print(json.dumps(dict(head=head,boot=h['boot_id'],groups_and_sessions=len(groups),no_julia=True,conflicts=h['conflicts'])))
