from pathlib import Path
import sys,shutil,subprocess
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-epsilon-bound-auxiliary/2026-10-28');sys.path.insert(0,str(D));import common_qualified as c
for n in ['RED-run/audit.json','RED-run/result-review.json']:
 r=c.read(n);c.need(r['accepted'] and not r.get('findings',[]),'accepted originalRED '+n)
c.unchanged();shutil.copytree(D/'RED',D/'GREEN');changes=[v for v in c.read('changes.json') if v['variant'] in c.read('test-gates.json')['accepted_variants']];names=set()
for ch in changes:
 p=D/'GREEN'/ch['file'];s=p.read_text();c.need(s.count(ch['old'])==1,'unique production region');p.write_text(s.replace(ch['old'],ch['new']));names.add(ch['file'])
p=D/'GREEN/test/runtests.jl';p.write_text(p.read_text()+'\ninclude("generic_epsilon_bound_auxiliary_tests.jl")\n');names.update(['test/generic_epsilon_bound_auxiliary_tests.jl','test/runtests.jl']);names=sorted(names)
for n in names:
 p=D/'GREEN'/n
 if n.startswith('src/'):
  s=p.read_text()
  for ch in reversed(changes):
   if ch['file']==n:c.need(s.count(ch['new'])==1,'unique exact inverse');s=s.replace(ch['new'],ch['old'])
  c.need(s==(D/'baseline'/n).read_text(),'source inverse '+n)
 q=D/'baseline'/n if (D/'baseline'/n).exists() else Path('/dev/null')
 r=subprocess.run(['/usr/bin/git','diff','--no-index','--check',str(q),str(p)],capture_output=True,text=True);c.need(r.returncode in [0,1] and not r.stdout and not r.stderr,'strict whitespace '+n)
c.put('source-inverse.json',dict(accepted=True,names=names,candidate_sha256={n:c.sha(D/'GREEN'/n) for n in names},whole_stage={str(p.relative_to(D/'GREEN')):c.sha(p) for p in (D/'GREEN').rglob('*') if p.is_file()},production_baseline=c.TARGET,all_numerical_checks_retained=True,no_added_scans_solves_copies=True))
print('exact productionstage',names)
