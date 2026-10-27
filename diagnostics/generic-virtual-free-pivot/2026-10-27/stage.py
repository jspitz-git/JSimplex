from pathlib import Path
import json,sys,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-virtual-free-pivot/2026-10-27');sys.path.insert(0,str(D));import common_ready as c
c.need(c.read('RED-ready-run/audit.json')['accepted'] and c.read('RED-ready-run/result-review.json')['accepted'],'witnessed accepted original RED before candidate')
c.unchanged();shutil.copytree(D/'RED',D/'GREEN');shutil.copyfile(D/'new-test-reviewed.jl',D/'GREEN/test/generic_virtual_free_pivot_tests.jl');changes=c.read('changes.json');names=set()
for change in changes:
 n='src/'+change['file'];p=D/'GREEN'/n;s=p.read_text();c.need(s.count(change['old'])==1,'one region '+n);p.write_text(s.replace(change['old'],change['new']));names.add(n)
r=D/'GREEN/test/runtests.jl';s=r.read_text();line='include("generic_virtual_free_pivot_tests.jl")\n';r.write_text(s+'\n'+line);names.update(['test/generic_virtual_free_pivot_tests.jl','test/runtests.jl']);names=sorted(names)
for n in names:
 if n in ['test/generic_virtual_free_pivot_tests.jl','test/runtests.jl']:continue
 s=(D/'GREEN'/n).read_text()
 for ch in reversed(changes):
  if 'src/'+ch['file']==n:c.need(s.count(ch['new'])==1,'inverse region');s=s.replace(ch['new'],ch['old'])
 c.need(s==(D/'baseline'/n).read_text(),'exact inverse '+n)
c.put('source-inverse.json',dict(accepted=True,names=names,candidate_sha256={n:c.sha(D/'GREEN'/n) for n in names},whole_stage={str(p.relative_to(D/'GREEN')):c.sha(p) for p in (D/'GREEN').rglob('*') if p.is_file()},production_baseline=c.TARGET,all_numerical_checks_retained=True,no_added_scans_solves_copies=True))
shutil.copyfile(__file__,D/'stage.py');print(names)
