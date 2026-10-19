"""One offline amendment: exact GREEN2 import-test lineage, no Julia."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;R=D.parents[3];G=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-GREEN2-PREPARATION')
Q=R/'docs/superpowers/plans/2026-10-19-direct-bg-export-specialization.md';A=D/'SELF-REVIEW.md'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text())
def require(v,m):
 if not v:raise RuntimeError(m)
checks={}
def ck(v,n):checks[n]=bool(v)
old='**Consumes:** the four frozen workspace candidate files; structural tests and the actual accepted GREEN2 lifecycle test source selected by its sealed manifest (including the sole `sum(...;init=0)` fix). Bind the actual executed test path and hash; do not silently use the older unfixed candidate test. Reference packed DIRECT stage and fixtures remain byte-identical.'
new='**Consumes:** the four frozen workspace candidate files and unchanged `workspace-tests.jl` and `lifecycle-tests.jl` under `diagnostics/direct-bg-export-workspace/reproduce`. The accepted GREEN2 import test is specifically `diagnostics/direct-bg-export-workspace-harness-fix/reproduce/import-tests.jl`, SHA256 `628a74265bc5ed75e0a9507b9a7f3f453ba76d413ccbcb8a90e177e9e2329260`, containing the sole `sum(...;init=0)` fix. Bind this exact path through GREEN2 `inverse.json`, the top-level `driver.jl` include and the accepted `runs/green2-300/sealed.json` inventory. It is a separately included test file, not part of the 79-file GREEN stage. Preserve the older unfixed import test; do not use it for the new suite. Reference packed DIRECT stage and fixtures remain byte-identical.'
old_a='The actual corrected GREEN2 lifecycle-test source must be used in Task1, while its older unfixed counterpart remains preserved.'
new_a='Task1 must use the corrected GREEN2 import test from `diagnostics/direct-bg-export-workspace-harness-fix/reproduce/import-tests.jl`, bound by the actual driver include and sealed inventory. The original lifecycle test is unchanged; the older unfixed import test remains preserved.'
q=Q.read_text();a=A.read_text();require(q.count(old)==1 and a.count(old_a)==1,'Unexpected original text')
inv=rd(G/'inverse.json');am=Path(inv['amended']);original=Path(inv['original']);driver=G/'driver.jl';sealed=G/'runs/green2-300/sealed.json';j=rd(sealed)
ck('GREEN2 lifecycle test source' in q and 'GREEN2 import test is specifically' not in q,'RED_wrong_test_selection_observed')
ck(sha(am)==inv['amended_sha256']=='628a74265bc5ed75e0a9507b9a7f3f453ba76d413ccbcb8a90e177e9e2329260' and sha(original)==inv['original_sha256'],'actual_import_hashes')
ck(original.read_text().replace(inv['before'],inv['after'])==am.read_text() and original.read_text().count(inv['before'])==1,'sole_original_import_fix')
ck('include("'+str(am)+'")' in driver.read_text() and 'include("'+str(original)+'")' not in driver.read_text(),'actual_amended_import_include')
life=R/'diagnostics/direct-bg-export-workspace/reproduce/lifecycle-tests.jl'
ck('include("'+str(life)+'")' in driver.read_text(),'unchanged_lifecycle_include')
ck(all(j['inventory'][str(p)]['sha256']==sha(p) for p in [am,original,driver,life]),'accepted_seal_actual_test_bindings')
require(all(checks.values()),'Pre-amendment gates failed')
for p,name in [(Q,'plan.before-review.md'),(A,'self-review.before-review.md')]:
 with (D/name).open('xb') as f:f.write(p.read_bytes())
Q.write_text(q.replace(old,new));A.write_text(a.replace(old_a,new_a))
ck(Q.read_text().replace(new,old)==q and A.read_text().replace(new_a,old_a)==a,'exact_two_text_amendments_only')
ck('GREEN2 lifecycle test source' not in Q.read_text() and new in Q.read_text() and new_a in A.read_text(),'GREEN_explicit_import_lineage')
mapping={str(Q):str(D/'plan.before-review.md'),str(A):str(D/'self-review.before-review.md')}
source=rd(D/'source-check.json')
ck(all(sha(Path(mapping.get(p,p)))==s for p,s in source['sha256'].items()),'original185bindings_preserved_with_explicit_map')
files=[Q,A,D/'plan.before-review.md',D/'self-review.before-review.md',D/'source-check.json',Path(__file__),G/'inverse.json',driver,sealed,am,original,life]
out=dict(all_passed=all(checks.values()),checks=checks,historical_path_map=mapping,sha256={str(p):sha(p) for p in files},scope='Only test-lineage wording repaired; initial literal GREEN2 gate was insufficient, original PASS preserved')
with (D/'review-fix.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=out['all_passed'],checks=len(checks),bindings=len(files),failed=[k for k,v in checks.items() if not v])))
require(out['all_passed'],'Post-amendment failed; preserve')
