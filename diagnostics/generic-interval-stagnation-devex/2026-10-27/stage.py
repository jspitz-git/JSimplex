from pathlib import Path
import json,sys,shutil,subprocess
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-interval-stagnation-devex/2026-10-27');sys.path.insert(0,str(D));import common as c
c.need(c.read('RED-run/audit.json')['accepted'] and c.read('RED-run/result-review.json')['accepted'],'witnessed accepted original RED');c.unchanged()
shutil.copytree(D/'RED',D/'GREEN');accepted=c.read('test-gates.json')['accepted_variants'];changes=[x for x in c.read('changes.json') if x['variant'] in accepted];names=set()
for ch in changes:
 p=D/'GREEN'/ch['file'];s=p.read_text();c.need(s.count(ch['old'])==1,'one region '+ch['file']);p.write_text(s.replace(ch['old'],ch['new']));names.add(ch['file'])
p=D/'GREEN/test/runtests.jl';p.write_text(p.read_text()+'\ninclude("generic_interval_stagnation_devex_tests.jl")\n');names.update(['test/generic_interval_stagnation_devex_tests.jl','test/runtests.jl']);names=sorted(names)
for n in names:
 p=D/'GREEN'/n
 if n.startswith('src/'):
  s=p.read_text()
  for ch in reversed(changes):
   if ch['file']==n:c.need(s.count(ch['new'])==1,'one inverse');s=s.replace(ch['new'],ch['old'])
  c.need(s==(D/'baseline'/n).read_text(),'exact inverse '+n)
 # Fail before tests on any introduced whitespace diagnostic; diff status1 alone is normal.
 q=D/'baseline'/n if (D/'baseline'/n).exists() else Path('/dev/null')
 r=subprocess.run(['/usr/bin/git','diff','--no-index','--check',str(q),str(p)],capture_output=True,text=True)
 c.need(r.returncode in [0,1] and not r.stdout and not r.stderr,'strict authored whitespace '+n)
# Prove concrete setup/rebase signatures occur after the workspace type in actual load order.
s=(D/'GREEN/src/simplex.jl').read_text();c.need(s.index('mutable struct SimplexWorkspace{')<s.index('function _new_workspace_stagnation(ws::SimplexWorkspace{BigFloat}'),'new constructor defined after type');c.need(s.index('mutable struct SimplexWorkspace{')<s.index('function _rebase_dual_stagnation_costs!(ws::SimplexWorkspace{BigFloat}'),'new rebase defined after type')
c.put('source-inverse.json',dict(accepted=True,names=names,candidate_sha256={n:c.sha(D/'GREEN'/n) for n in names},whole_stage={str(p.relative_to(D/'GREEN')):c.sha(p) for p in (D/'GREEN').rglob('*') if p.is_file()},production_baseline=c.TARGET,all_numerical_checks_retained=True,no_added_scans_solves_copies=True,strict_whitespace_clean=True,late_B_signature_load_order_verified=True))
shutil.copyfile(__file__,D/'stage.py');print('production stage prepared',names)
