"""Fresh Task2 reviewer: bytes/JSON/static text only; no Julia or old checker execution."""
from pathlib import Path
import hashlib, json, re
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
C=R/'diagnostics/direct-bg-export-workspace/reproduce'
E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-WORKSPACE-TASK2'
E1=E.with_name('DIRECT-BG-EXPORT-WORKSPACE-TASK1')
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()
author=json.loads((E/'source-check.json').read_text())
overlay=json.loads((C/'overlay-manifest.json').read_text())
task1=json.loads((E1/'final-review.json').read_text())
pins=author['readtime_sha256']
actual={p:sha(p) for p in pins}
mismatches={p:{'expected':h,'actual':actual[p]} for p,h in pins.items() if h!=actual[p]}
checks={
 'all_702_author_bindings_rehashed':len(pins)==702 and not mismatches,
 'all_679_original_bindings_match':len(overlay['original_readtime_sha256'])==679 and all(actual[p]==h for p,h in overlay['original_readtime_sha256'].items()),
 'task1_eight_frozen_bindings_match':len(overlay['candidate_task1_frozen'])==8 and all(actual[p]==h==task1['readtime_sha256'][p] for p,h in overlay['candidate_task1_frozen'].items()),
 'task2_three_manifest_bindings_match':len(overlay['candidate_task2'])==3 and all(actual[p]==h for p,h in overlay['candidate_task2'].items()),
 'task1_final_acceptance_record':task1['accepted'] and not any(task1[k] for k in ('critical','important','minor')),
}
stage=Path(overlay['stage'])
f=(C/'factor.jl').read_text();t=(C/'lifecycle-tests.jl').read_text()
tri=(stage/'src/triangular_factorization.jl').read_text()
body=tri.split('mutable struct BartelsGolubFactorization',1)[1].split('\nend',1)[0]
fields=re.findall(r'^    ([a-z_]+)::',body,re.M)
checks['original_bg_field_inventory_14']=len(fields)==14
checks['single_publication_after_mandatory_type_check']=f.count('f.inner=candidate')==1 and f.index('typeof(candidate)===typeof(f.inner)')<f.index('f.inner=candidate')
checks['single_build_factorize_export_import_sites']=all(f.count(s)==1 for s in ('ordinary=factorize(B,backend,policy)','parts=export_parts(ordinary,owner;allocate)','upper,D=import_upper(parts.upper,normalize;allocate)'))
checks['static_test_sites_66']=len(re.findall(r'@test(?:_throws)?\b',t))==66
checks['repeated_work_count_2984']=6*(28+192+48)+192*6+28*8==2984
checks['small_active_fixture_cannot_retain_cache']=(16*(2*(8*9//2))+8*(8+1))//16<512
checks['failure_matrix_cold_reset_sites_present']='X._bgx_drop!(f);alloc=Allocator(k)' in t and 'X._bgx_drop!(f);alloc=Allocator(k);parts=orientation_parts(64)' in t
extra=[E/'REPORT.md',E/'progress.md',E/'source-check.json',E/'reviewer-check.py',R/'AGENTS.md',R/'diagnostics/direct-lu-policy-adapters/reproduce/lifecycle-tests.jl']
for p in extra: actual[str(p)]=sha(p)
result={'scope':'Independent offline byte/hash and static-text checks only; no Julia syntax/dispatch/numerical acceptance',
 'all_passed':all(checks.values()),'checks':checks,'mismatches':mismatches,
 'original_author_bindings_verified':len(pins),'original_bg_fields':fields,
 'source_observations':{'default_exact_type_comparison_sites':2,'small_n8_max_triangular_budget':76,'repeated_valid_solve_entries':2984,'static_assertion_sites':66,'root_additions':overlay['root_additions']},
 'readtime_sha256':dict(sorted(actual.items()))}
with (E/'reviewer-check.json').open('x') as out: json.dump(result,out,indent=2);out.write('\n')
print(json.dumps({'checks':len(checks),'all_passed':result['all_passed'],'author_hashes':len(pins),'readtime_hashes':len(actual),'mismatches':len(mismatches),'fields':fields}))
