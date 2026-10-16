"""One bounded documentation correction; original evidence stays immutable."""
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent;R=P.parents[3];plan=R/'docs/superpowers/plans/2026-10-16-direct-lu-policy-adapters.md'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def save(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
need((P/'review-initial.json').exists(),'Preserve initial review first')
s=plan.read_text();before=P/'plan.before-review'
with before.open('xb') as f:f.write(plan.read_bytes())
old1='failed singular/resized refactors';old2='Use the explicit internal `factorize` keyword with a test-local throwing counter closure; assert zero calls on rejected requests.'
need(old1 in s and old2 in s,'Original two ambiguous statements')
s=s.replace('successful/singular/resized refactor','successful same-size and resized refactors plus transactional singular failure')
s=s.replace(old1,'transactional singular failures and successful resized refactors (new dimension/work buffers, saved copies retain their old dimension and values)')
s=s.replace(old2,'For Float64 only, use the explicit internal `factorize` keyword with a test-local throwing counter closure; assert zero calls on rejected empty/nonempty requests. For Float32, BigFloat256 and Rational{BigInt}, use negative ArgumentError tests of the generic four-argument factory plus an exact source/inverse check of current `Factor(B,backend,policy)` forwarding and `_factorize_basis(B,Val(:markowitz),policy)` rejecting before the ordinary two-argument call. This is source-supported pre-work rejection for generic types, not runtime call-count evidence; do not add a generic injection seam or overwrite production methods.')
plan.write_text(s)
checks=dict(original_ambiguities_preserved=old1 in before.read_text() and old2 in before.read_text(),singular_and_resize_distinguished=old1 not in s and 'successful resized refactors (new dimension/work buffers' in s,float64_counter_scope='For Float64 only' in s,generic_source_not_runtime_count='not runtime call-count evidence' in s,no_generic_seam='do not add a generic injection seam' in s,unchanged_spec=True)
need(all(checks.values()),'Fix checks')
save(P/'review-fix.json',dict(all_passed=True,checks=checks,mapping=dict(original=str(plan),sha256=sha(before),preserved=str(before)),sha256={str(p):sha(p) for p in [plan,before,Path(__file__)]}))
old=json.loads((P/'source-inputs.json').read_text());pins={n:(sha(plan) if n==str(plan) else h) for n,h in old['sha256'].items()}
for p in [before,Path(__file__),P/'review-fix.json',P/'source-inputs.json',P/'review-initial.json',P/'review-initial.md',P/'close.py',P/'publication.py']:pins[str(p)]=sha(p)
save(P/'source-inputs-reviewed.json',dict(scope='Corrected readtime planning inputs; original manifest frozen with one explicit old-plan mapping',sha256=pins))
print('Documentation correction6PASS;',len(pins),'canonical bindings; no source/Julia changes')
