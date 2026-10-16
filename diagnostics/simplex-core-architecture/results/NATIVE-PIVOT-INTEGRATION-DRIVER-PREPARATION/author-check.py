"""New independent-of-old-runners author closure check; no numerical execution."""
from common import *
from control import config,predecessor,verify_review
pins=Q/'preparation-pins.json';m=rd(pins);v=rd(Q/'review-final.json')
verify_review(v,pins,list(m['sha256'])+[str(pins)],'offline preparation')
require(bindings(m),'Preparation drift')
require(all(sha(path(n))==h for n,h in v.get('evidence_sha256',{}).items()),'Reviewer evidence drift')
files,groups=predecessor('integration');h=host();verify_host(h)
checks=dict(review=True,required=set(m['sha256'])==set(rd(Q/'required-paths.json')['paths']),
 actual520=len(rd(Q/'actual-baseline.json')['sha256'])==520 and all(sha(R/n)==s for n,s in rd(Q/'actual-baseline.json')['sha256'].items()),
 source_original=rd(Q/'source-check.json')['all_passed'] and bindings(rd(Q/'source-check.json')),
 offline_green=rd(Q/'offline-GREEN.json')['all_passed'] and len(rd(Q/'offline-GREEN.json')['checks'])==35,
 old_red=rd(Q/'offline-RED.json')['all_passed'] is False,
 no_stage=not Path(config('integration')['stage']).exists(),no_runs=not (Q/'runs').exists(),
 groups216=len(groups)==216 and not h['matches'],
 unchanged_continuation=sha(STATUS)==sha(Q/'STATUS.md.before-driver') and sha(ROAD)==sha(Q/'roadmap.md.before-driver'),
 selected_only='extracted-factor and raw auxiliary LU work excluded' in (Q/'driver.jl').read_text(),
 fixed_duration=config('integration')['seconds']==60,
 fixed_suite='162 assertions' in (Q/'REPORT.md').read_text(),
 prep_not_stage='read-time' in m['scope'])
save(Q/'author-check.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in [pins,Q/'review-final.json',Q/'REPORT.md',Q/'WORK-AND-ADMISSION.md',Q/'source-check.json',Q/'offline-GREEN.json',Q/'continuation-text.md',Q/'finalize.py',Q/'publication.py',Q/'author-check.py']},scope='Fresh offline bindings/closure check; no prior runner rerun or Julia'))
require(all(checks.values()),'Author closure check failed; preserve');print(dict(checks=len(checks),pins=len(m['sha256']),review=len(v['sha256'])))
