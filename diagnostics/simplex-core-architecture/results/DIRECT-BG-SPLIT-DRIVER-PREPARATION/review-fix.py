"""One bounded ledger correction; no Julia, old checks or manifest generator execution."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
for n in ['work-ledger.json','required-paths.json','preparation-pins.json']:
 with (D/(n+'.before-review')).open('xb') as f:f.write((D/n).read_bytes())
w=json.loads((D/'work-ledger.json').read_text());old=w['new_storage_only_pair_work']['full_partition_token_scans']
if old!='after each129assignments and3rotations, plus finalmerge and explicit checks; O(n+C+R+K), test-only':raise RuntimeError('Unexpected original ledger')
w['new_storage_only_pair_work']['full_partition_token_scans']='After each of 129 assignments and 3 rotations, plus final merge and explicit checks: O(n+C+R+K) traversal, plus two n-entry Int vector conversions and sorts in _sbu_check and invariant bookkeeping allocations per check. Overall work is not asserted linear; sort implementation and allocations remain unmeasured. Test-only.'
(D/'work-ledger.json').write_text(json.dumps(w,indent=2)+'\n')
a='''# Preserved initial review and bounded ledger correction

Initial review R1 found an incomplete test-only work bound. The partition traversal is O(n+C+R+K), but `_sbu_check` also constructs two n-entry Int vectors and sorts them, with invariant bookkeeping allocations. The corrected field states those additional costs and makes no overall linear or measured-allocation claim.

Only `work-ledger.json` is corrected. Candidate, tests, driver, numeric counts and source-derived callback counts are unchanged. Original `derive-counts.py` remains frozen and its emitted ledger field is superseded by this amendment; it is never rerun. The original source-check.json work-ledger binding maps ONLY to work-ledger.json.before-review. All its other bindings remain current. Initial preparation-pins.json maps work-ledger.json to its before-review file and required-paths.json to required-paths.json.before-review; other original pins remain current. Initial review's preparation-pins.json binding maps ONLY to preparation-pins.json.before-review. These mappings apply only on exact hash equality.

Current required-paths/preparation-pins include the corrected ledger and these three preserved originals, this fix script/result and amendment. This is offline preparation, not a launch pin or numerical admission. No Julia, seal, reservation, run or old checker execution.
'''
with (D/'REVIEW-AMENDMENT.md').open('x') as f:f.write(a)
oldw=json.loads((D/'work-ledger.json.before-review').read_text());oldw['new_storage_only_pair_work']['full_partition_token_scans']=w['new_storage_only_pair_work']['full_partition_token_scans']
checks=dict(red_original_bound_incomplete='O(n+C+R+K), test-only' in old,green_conversions_explicit='two n-entry Int vector conversions' in w['new_storage_only_pair_work']['full_partition_token_scans'],green_sorting_explicit='sorts' in w['new_storage_only_pair_work']['full_partition_token_scans'],green_no_total_linear_claim='not asserted linear' in w['new_storage_only_pair_work']['full_partition_token_scans'],only_single_field_changed=oldw==w,no_runs=not (D/'runs').exists())
items=['review-fix.py','REVIEW-AMENDMENT.md','work-ledger.json','work-ledger.json.before-review','required-paths.json.before-review','preparation-pins.json.before-review']
save(D/'review-fix.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(D/n):sha(D/n) for n in items},scope='Bounded offline ledger correction only. Original evidence preserved.'))
if not all(checks.values()):raise RuntimeError('Fix failed')
pins=json.loads((D/'preparation-pins.json.before-review').read_text());names=set(pins['sha256'])|{str(D/n) for n in items+['review-fix.json']}
(D/'required-paths.json').write_text(json.dumps(dict(scope='Current exact preparation inputs after R1; original membership preserved, no numerical admission',paths=sorted(names)),indent=2)+'\n')
pins['scope']='Current offline preparation after R1; original pins preserved; no numerical admission or launch'
pins['sha256']={n:sha(Path(n)) for n in sorted(names)}
(D/'preparation-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
print(json.dumps(dict(all_passed=True,checks=len(checks),current_pins=len(names))))
