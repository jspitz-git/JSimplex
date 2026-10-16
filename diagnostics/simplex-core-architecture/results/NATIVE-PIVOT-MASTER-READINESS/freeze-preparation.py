from control import *
validate_environment();prod=validate_production(False)
require(not (D/'runs').exists(),'No numerical attempt should exist')
old=rd(P/'review-final.json');require(old['accepted'] is True and old['findings']==[] and bindings(old),'Previous review drift')
files={Path(n) for n in old['sha256']}|{P/'review-final.json',P/'closure.json',P/'publication.json'}
# Current predecessor continuation keys are represented ONLY by preserved copies.
for rec in [P/'closure.json',P/'publication.json']:
 for n,h in rd(rec)['sha256'].items():
  p=path(n)
  if p==R/'diagnostics/simplex-core-architecture/STATUS.md':p=D/'STATUS.md.before-readiness'
  if p==R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md':p=D/'roadmap.md.before-readiness'
  require(sha(p)==h,'Predecessor closure/publication drift '+n);files.add(p)
save(D/'config-preview.json',{k:config(k) for k in ['master300','master600']})
files|={p for p in D.iterdir() if p.is_file()}|set(prod)|{Path(n) for n in rd(D/'runtime-inputs.json')['inventory']}
for n,v in rd(D/'runtime-inputs.json')['inventory'].items():require(sha(n)==v['sha256'] and str(Path(n).resolve())==v['resolved'],'Runtime drift')
paths=sorted(str(p) for p in files);save(D/'required-paths.json',dict(paths=paths))
save(D/'preparation-pins.json',dict(scope='Offline readiness inputs, not a launch seal',sha256={p:sha(p) for p in paths}))
print('Frozen',len(paths),'preparation inputs; no stage/attempt/reservation')
