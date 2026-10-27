from pathlib import Path
import json,sys,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-stagnation-unit-seed/2026-10-27');sys.path.insert(0,str(D));import common_reviewed as c
c.need(c.read('RED-run/audit.json')['accepted'] and c.read('RED-run/result-review.json')['accepted'],'witnessedacceptedRED')
c.unchanged();shutil.copytree(D/'RED',D/'GREEN');changes=c.read('changes.json');names=set()
for ch in changes:
 n=ch['file'];p=D/'GREEN'/n;s=p.read_text();c.need(s.count(ch['old'])==1,'one region '+n);p.write_text(s.replace(ch['old'],ch['new']));names.add(n)
p=D/'GREEN/test/runtests.jl';p.write_text(p.read_text()+'\ninclude("generic_stagnation_unit_seed_tests.jl")\n');names.update(['test/generic_stagnation_unit_seed_tests.jl','test/runtests.jl']);names=sorted(names)
for n in names:
 if not n.startswith('src/'):continue
 s=(D/'GREEN'/n).read_text()
 for ch in reversed(changes):
  if ch['file']==n:c.need(s.count(ch['new'])==1,'one inverse');s=s.replace(ch['new'],ch['old'])
 c.need(s==(D/'baseline'/n).read_text(),'exact inverse '+n)
c.put('source-inverse.json',dict(accepted=True,names=names,candidate_sha256={n:c.sha(D/'GREEN'/n) for n in names},whole_stage={str(p.relative_to(D/'GREEN')):c.sha(p) for p in (D/'GREEN').rglob('*') if p.is_file()},production_baseline=c.TARGET,all_numerical_checks_retained=True,no_added_scans_solves_copies=True));shutil.copyfile(__file__,D/'stage.py');print(names)
