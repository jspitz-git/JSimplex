"""One-shot offline preparation inventory; no seal or Julia."""
from control import *
import ast
validate_environment();validate_sources();extra,groups=predecessor('cost1-300');h=full_host(groups)
require(not h['matches'] and not guard.pressure(guard.memory()),'Fresh host/resources')
require(rd(D/'offline-tests.json')['all_passed'] and rd(D/'prefix-tests.json')['all_passed'] and rd(D/'source-check.json')['all_passed'],'Offline checks')
require(rd(D/'config.json')=={p:config(p) for p in ['cost1-300','cost2-300','cost1-600','cost2-600']},'Configs')
require(not (D/'runs').exists(),'No phase')
for p in D.glob('*.py'):ast.parse(p.read_text())
G=D.parent/'DIRECT-BG-DYNAMIC-GREEN';maps=[]
for rec in [G/'closure.json',G/'publication.json']:
 for field in ['sha256','git_blobs']:
  for n,v in rd(rec).get(field,{}).items():
   target=path(n);old=target
   if target==R/'diagnostics/simplex-core-architecture/STATUS.md':old=D/'STATUS.md.before-COST'
   if target==R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md':old=D/'roadmap.md.before-COST'
   require((sha(old) if field=='sha256' else git('hash-object','--',str(old)))==v,'GREEN prior binding')
   if old!=target:maps.append(dict(record=str(rec),field=field,key=n,value=v,preserved=str(old)))
require(len(maps)==6,'Six continuation maps')
save(D/'author-check.json',dict(all_passed=True,checks=dict(offline91=True,prefix23=True,source16=True,source_runtime_stage=True,green_lineage=True,exact_four_configs=True,python_syntax=True,continuation_maps6=True,no_phase=True,fresh_host=True),host=h,maps=maps,scope='Offline only; no Julia syntax or runtime evidence'))
files={str(p) for p in D.iterdir() if p.is_file()}|{str(p) for p in C.iterdir() if p.is_file()}|set(extra)|set(rd(D/'runtime-inputs-complete.json')['inventory'])
files|={str(root/n) for label,root in [('diagnostic',R),('production',W)] for n in rd(D/'baseline.json')[label]}
stage=rd(D/'stages.json')['cost'];files|={str(Path(stage['path'])/n) for n in stage['sha256']}
files|={str(R/'docs/superpowers'/k/'2026-10-16-direct-bg-dynamic-upper.md') for k in ['plans','specs']}
files|=set(rd(D/'source-inverse.json')['originals'])|set(rd(D/'source-inverse.json')['probe'][n]['original'] for n in ['probe-slots.jl','probe-bg.jl'])
files.add(str(D/'required-paths.json'));save(D/'required-paths.json',dict(paths=sorted(files)))
save(D/'preparation-pins.json',dict(scope='Offline cost preparation, NOT phase seal or execution admission',sha256={n:sha(n) for n in sorted(files)}))
require(bindings(rd(D/'preparation-pins.json')),'Inventory hashes')
print('Author10PASS;',len(files),'readtime hashes; no Julia')
