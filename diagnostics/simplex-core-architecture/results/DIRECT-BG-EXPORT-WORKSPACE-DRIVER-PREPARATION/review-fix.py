"""One offline R1 amendment; original rejection and manifest preserved. No Julia."""
from control import *
import shutil
checks={}
def ck(v,n):
 checks[n]=bool(v)
 require(v,n)
oldpins=rd(D/'preparation-pins.json');oldreq=rd(D/'required-paths.json');oldreview=rd(D/'review.json')
ck(oldreview['accepted'] is False and len(oldreview['findings'])==1,'one_initial_rejection_preserved')
ck(bindings(oldpins) and set(oldpins['sha256'])==set(oldreq['paths']),'original1858_actual_hashes')
ck(len(oldpins['sha256'])==1858,'original_manifest_count')
fixture=R/'diagnostics/direct-lu-policy-adapters/reproduce/fixtures.jl'
ck(str(fixture) not in oldpins['sha256'],'RED_fixture_missing_initial_manifest')
expected='835b6e4241705b4c7a6a2625c904999ffe30e90ec99c937d257cbe2a2c289517'
for task in ('TASK1','TASK2'):
 previous=rd(D.with_name('DIRECT-BG-EXPORT-WORKSPACE-'+task)/'final-review.json')
 ck(previous['readtime_sha256'][str(fixture)]==expected and sha(fixture)==expected,'accepted_'+task+'_fixture_identity')
ck('include("../../direct-lu-policy-adapters/reproduce/fixtures.jl")' in (C/'import-tests.jl').read_text(),'literal_transitive_include')
ck('include(' not in fixture.read_text(),'fixture_no_further_include')
mapping={}
for n in ['required-paths.json','preparation-pins.json','review.json','review.md']:
 before=D/(n+'.before-R1');shutil.copyfile(D/n,before);mapping[str(D/n)]=str(before)
ck(all(sha(mapping.get(n,n))==h for n,h in oldreview['sha256'].items()),'original_review_all1859_bindings_preserved')
ck(bindings(rd(D/'source-check.json')),'initial_author_checks_all_bytes_unchanged')
# Remove canonical rejected review only after exact preservation; final reviewer writes a new file.
(D/'review.json').unlink();(D/'review.md').unlink()
ck(not (D/'runs').exists(),'no_seal_launch_output')
record=dict(all_passed=True,checks=checks,before_mapping=mapping,sha256={str(fixture):sha(fixture),**{str(p):sha(p) for p in [D/'review-fix.py',D/'AMENDMENT.md',*(Path(x) for x in mapping.values())]}},scope='R1 additive transitive fixture pin, no candidate/test/driver/control change')
save(D/'review-fix.json',record)
# Exact additional names supplied as a literal in the reviewed amendment source.
EXTRA_NAMES = ['review-fix.py', 'review-fix.json', 'AMENDMENT.md', 'required-paths.json.before-R1', 'preparation-pins.json.before-R1', 'review.json.before-R1', 'review.md.before-R1', 'independent-review-check.py', 'independent-review-check-initial-error.json', 'independent-review-check-v2.py', 'independent-review-check-v2.json']
paths=sorted(set(oldreq['paths'])|{str(fixture)}|{str(D/n) for n in EXTRA_NAMES})
# Originals survive byte-exactly under before-R1; only canonical manifests are replaced.
(D/'required-paths.json').write_text(json.dumps(dict(scope='R1 corrected exact offline preparation inputs; not numerical admission',paths=paths),indent=2)+'\n')
(D/'preparation-pins.json').write_text(json.dumps(dict(scope='R1 corrected offline preparation, NOT numerical admission or launch',sha256={p:sha(p) for p in paths}),indent=2)+'\n')
print(json.dumps(dict(all_passed=True,checks=len(checks),bindings=len(paths),fixture_sha256=sha(fixture))))
