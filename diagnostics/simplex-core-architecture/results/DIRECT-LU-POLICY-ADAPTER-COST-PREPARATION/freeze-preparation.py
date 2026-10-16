"""One-shot offline canonical inventory and source/lineage checks; no phase seal."""
from control import *
import ast
G=D.parent/'DIRECT-LU-POLICY-ADAPTER-GREEN'
validate_environment();validate_sources();extra,groups=predecessor('cost1-300');h=full_host(groups)
require(not h['matches'] and not guard.pressure(guard.memory()),'Fresh host')
require(rd(D/'offline-tests-2.json')['all_passed'] and rd(D/'prefix-tests.json')['all_passed'],'Offline checks')
require(rd(D/'config.json')=={p:config(p) for p in ['cost1-300','cost2-300','cost1-600','cost2-600']},'Exact configs')
require(not (D/'runs').exists(),'No runtime phase yet')
for n,v in rd(D/'lineage.json')['inputs'].items():require(sha(n)==v==sha(D/Path(n).name),'Immutable input tokens')
maps=[]
for rec in [G/'closure.json',G/'publication.json']:
 for n,v in rd(rec)['sha256'].items():
  target=R/n
  if n=='diagnostics/simplex-core-architecture/STATUS.md':target=D/'STATUS.md.before-cost'
  if n=='docs/superpowers/plans/2026-10-11-simplex-core-architecture.md':target=D/'roadmap.md.before-cost'
  require(sha(target)==v,'GREEN closure/publication drift '+n)
  if target!=R/n:maps.append(dict(record=str(rec),original=n,sha256=v,preserved=str(target)))
require(len(maps)==4,'Continuation maps')
for p in D.glob('*.py'):ast.parse(p.read_text())
save(D/'author-check.json',dict(all_passed=True,checks=dict(offline91=True,prefix17=True,source_runtime_stage=True,green_lineage=True,exact_four_configs=True,immutable_inputs=True,python_syntax_only=True,continuation_maps4=True,no_phase=True,fresh_host=True),prior_maps=maps,host=h,scope='Offline source/readtime; no Julia or executable runtime qualification'))
files={str(p) for p in D.iterdir() if p.is_file()}|{str(p) for p in C.iterdir() if p.is_file()}|{str(p) for p in G.iterdir() if p.is_file()}|set(extra)
files|={str(R/'docs/superpowers'/k/'2026-10-16-direct-lu-policy-adapters.md') for k in ['plans','specs']}
files.add(str(D/'required-paths.json'));files.discard(str(D/'preparation-pins.json'))
paths=sorted(files);save(D/'required-paths.json',dict(paths=paths));save(D/'preparation-pins.json',dict(scope='Offline Task3 preparation, not runtime admission',sha256={n:sha(n) for n in paths}))
require(bindings(rd(D/'preparation-pins.json')),'Preparation hashes')
print('Offline author10PASS; canonical',len(paths),'pins. No Julia.')
