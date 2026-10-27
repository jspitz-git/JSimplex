from pathlib import Path
import sys,json,shutil,hashlib
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-local/2026-10-27');sys.path.insert(0,str(D));import common_next as c
arm=sys.argv[1];c.need(arm in ['RED','GREEN'],'stage');c.unchanged()
review=json.loads((D/'comparison-2/result-review.json').read_text());c.need(review['accepted'] is True and review['findings']==[],'accepted comparison')
for p,h in review['bindings'].items():c.need(c.sha(p)==h,'result binding')
if arm=='RED':
 c.put('before-RED-host.json',c.host(json.loads((D/'comparison-2/audit-host.json').read_text())['groups']))
 shutil.copyfile(D/'new-test-draft.jl',D/'new-test.jl');shutil.copytree(D/'baseline',D/'RED');shutil.copyfile(D/'new-test.jl',D/'RED/test/generic_quality_local_tests.jl')
 path=D/'RED/test/runtests.jl';old=path.read_text();path.write_text(old+'\ninclude("generic_quality_local_tests.jl")\n')
else:
 r=json.loads((D/'RED-run/result-review.json').read_text());c.need(r['accepted'] and r['findings']==[],'accepted RED')
 for p,h in r['bindings'].items():c.need(c.sha(p)==h,'RED binding')
 c.put('before-GREEN-host.json',c.host(json.loads((D/'RED-run/audit-host.json').read_text())['groups']))
 shutil.copytree(D/'RED',D/'GREEN');changes=c.read('changes.json')
 for key in ['A','B','C']:
  v=changes[key];p=D/'GREEN/src'/v['file'];s=p.read_text();c.need(s.count(v['old'])==1,'one change '+key);p.write_text(s.replace(v['old'],v['new']))
 for name in ['simplex_numerics.jl','primal_updates.jl']:
  s=(D/'GREEN/src'/name).read_text()
  for key in ['C','B','A']:
   v=changes[key]
   if v['file']==name:c.need(s.count(v['new'])==1,'one inverse '+key);s=s.replace(v['new'],v['old'])
  c.need(s==(D/'baseline/src'/name).read_text(),'whole-source inverse '+name)
 stage=D/'GREEN';green={str(p.relative_to(stage)):c.sha(p) for p in stage.rglob('*') if p.is_file()};baseline=c.read('baseline-tree.json');names=sorted(n for n in green if n not in baseline or green[n]!=baseline[n]);c.need(names==['src/primal_updates.jl','src/simplex_numerics.jl','test/generic_quality_local_tests.jl','test/runtests.jl'],'exact4productionnames')
 c.put('source-inverse.json',dict(accepted=True,names=names,candidate_sha256={n:green[n] for n in names},whole_stage=green))
shutil.copyfile(__file__,D/('build-'+arm+'.py'));print(arm+' stage prepared; noJulia')
