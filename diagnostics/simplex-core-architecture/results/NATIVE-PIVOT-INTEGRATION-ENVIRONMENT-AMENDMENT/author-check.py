"""New author offline closure check; no historical scripts or numerical run."""
from control import *
m=rd(D/'preparation-pins.json');v=rd(D/'review-final.json')
verify_review(v,D/'preparation-pins.json',list(m['sha256'])+[str(D/'preparation-pins.json')],'offline preparation')
require(bindings(m),'Preparation changed')
require(all(sha(path(n))==h for n,h in v.get('evidence_sha256',{}).items()),'Review evidence changed')
validate_environment();h=host();verify_host(h);files,groups=predecessor('integration');cfg=config('integration')
checks=dict(review=True,exact_environment=True,required=set(m['sha256'])==set(rd(D/'required-paths.json')['paths']),
 actual520=len(rd(D/'actual-baseline.json')['sha256'])==520 and all(sha(R/n)==h for n,h in rd(D/'actual-baseline.json')['sha256'].items()),
 source17=rd(D/'source-check.json')['all_passed'] and len(rd(D/'source-check.json')['checks'])==17 and bindings(rd(D/'source-check.json')),
 offline17=rd(D/'offline-GREEN.json')['all_passed'] and len(rd(D/'offline-GREEN.json')['checks'])==17,
 no_stage=not Path(cfg['stage']).exists(),no_run=not (D/'runs').exists(),old_no_run=not (DRIVER/'runs').exists(),
 fresh216=len(groups)==216 and not h['matches'],unchanged_continuation=sha(STATUS)==sha(D/'STATUS.md.before-environment') and sha(ROAD)==sha(D/'roadmap.md.before-environment'),
 same_original_driver=cfg['command'][-4]==str(DRIVER/'driver.jl'),same60=cfg['seconds']==60)
save(D/'author-check.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in [D/'preparation-pins.json',D/'review-final.json',D/'REPORT.md',D/'continuation-text.md',D/'author-check.py',D/'finalize.py',D/'publication.py']},scope='Offline final integrity only; no numerical admission'))
require(all(checks.values()),'Author check failed; preserve');print(dict(checks=len(checks),pins=len(m['sha256']),review=len(v['sha256'])))
