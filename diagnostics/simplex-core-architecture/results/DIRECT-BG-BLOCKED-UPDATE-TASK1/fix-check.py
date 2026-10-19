from pathlib import Path
import hashlib,json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');C=R/'diagnostics/direct-bg-blocked-update/reproduce';Q=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-TASK1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with (Q/'fix-check.py').open('xb') as f:f.write(Path(__file__).read_bytes())
t=(C/'panel-tests.jl').read_text();p=(C/'panel.jl').read_text();old=(Q/'panel.jl.before-review').read_text();j=json.loads((Q/'source-check.json').read_text());rev=json.loads((Q/'review-initial.json').read_text());first=json.loads((Q/'review-tests-first.json').read_text())
def resolve(n):
 x=Path(n) if Path(n).is_absolute() else R/n
 return Q/(x.name+'.before-review') if x.parent==C else x
checks={
'initial_author_bindings_preserved':all(sha(resolve(n))==h for n,h in j['sha256'].items()),
'initial_review_bindings_preserved':all(sha(resolve(n))==h for n,h in rev['sha256'].items()),
'new_tests_before_probe':first['tests_sha256']==sha(C/'panel-tests.jl') and first['candidate_before_probe_sha256']==sha(Q/'panel.jl.before-review'),
'candidate_change_bounded':p==old.replace('function _bgb_apply!(ws,r::Int,b::Int,w::Int)','function _bgb_apply!(ws,r::Int,b::Int,w::Int,probe=nothing)').replace('swapped=J._pivot_magnitude(z)>J._pivot_magnitude(a)\n','swapped=J._pivot_magnitude(z)>J._pivot_magnitude(a)\n        # Optional cold observer; no trace stored by the unobserved kernel.\n        probe===nothing || probe(r+t-1,a,z,swapped)\n'),
'required_commit_acceptance':'if out.accepted' not in t and '@test out.accepted # rejection must not bypass' in t,
'predecision_and_masks':all(x in t for x in ['observed==pre','reinterpret(UInt64,a)','ws.touched[1:64,1:9]==touched']),
'history_both_directions':all(x in t for x in ['_apply_row_update!','_apply_transposed_row_update!','transpose(T)*v','.last==ws.steps[k].row']),
'computed_budget':all(x in t for x in ['values[11]==1152+Int(extra)','values[12]==1152','snapshot(f)==saved && f.row_columns_ready']),
'positive_fill_reuse_owners':all(x in t for x in ['for r in (1,9,17)','A[1,64]=2.0','indices.ids!==old.indices.ids','values[17]==2*(96-9)']),
'counter_witness':all(x in t for x in ['c.values[1]==sum','c.values[2]==128','values[18]==94','values[20]']),
'boundary_explicit':'Carrier tests intentionally hit generic no-op' in (C/'work-memory-ledger.md').read_text(),
}
result={'all_passed':all(checks.values()),'checks':checks,'sha256':{str(x):sha(x) for x in list(C.iterdir())+[Q/'REVIEW-FIX.md',Q/'fix-check.py',Q/'review-tests-first.json']},'scope':'Offline textual fix and preserved binding checks, no Julia validation'}
with (Q/'fix-check.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(checks))
if not result['all_passed']:raise SystemExit(1)
