from pathlib import Path
import hashlib
import json

R = Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
E = R / 'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-WORKSPACE-PLAN'
S = R / 'docs/superpowers/specs/2026-10-18-direct-bg-export-workspace.md'
P = R / 'docs/superpowers/plans/2026-10-18-direct-bg-export-workspace.md'
before = {str(S): E / 'spec.before-review.md', str(P): E / 'plan.before-review.md'}
bindings = {}
checks = {}
def read(p):
    p = Path(p)
    raw = p.read_bytes()
    bindings[str(p)] = hashlib.sha256(raw).hexdigest()
    return raw.decode()
def check(name, value):
    checks[name] = bool(value)
def verify_record(label, record, fields, mapped=False):
    for field in fields:
        for name, expected in record[field].items():
            p = before.get(name, Path(name)) if mapped else Path(name)
            read(p)
            check(label + ':' + field + ':' + name, bindings[str(p)] == expected)

author = json.loads(read(E / 'author-check.json'))
initial = json.loads(read(E / 'review.json'))
amendment = json.loads(read(E / 'amendment-check.json'))
verify_record('original-author', author, ['readtime_sha256'], True)
verify_record('initial-review', initial, ['readtime_sha256', 'evidence_sha256'], True)
verify_record('author-amendment', amendment, ['readtime_sha256'])
check('initial-rejection-preserved', initial['accepted'] is False and len(initial['findings']) == 2)
check('author-amendment-pass', amendment['all_passed'] is True and all(amendment['checks'].values()))
spec, plan = read(S), read(P)
stage = R / '.superpowers/sdd/2026-10-16-direct-lu-policy-adapters/driver-stages/green/src'
hh = read(stage / 'huangfu_hall_factorization.jl')
seal = json.loads(read(R / 'diagnostics/simplex-core-architecture/results/DIRECT-LU-POLICY-ADAPTER-COST-PREPARATION/runs/cost1-300/sealed.json'))
for name in ('direct-factor.jl', 'factor-export.jl', 'huangfu_hall_factorization.jl', 'markowitz_factorization.jl', 'triangular_factorization.jl', 'triangular_indices.jl', 'triangular_rows.jl', 'bartels_golub_rows.jl'):
    p = stage / name
    read(p)
    check('sealed:' + name, bindings[str(p)] == seal['inventory'][str(p)]['sha256'] and str(p.resolve()) == seal['inventory'][str(p)]['resolved'])
check('original-native-guard-order', hh.index('ldiv!(auxiliary,F,work)') < hh.index('all(isfinite,auxiliary) && any(!iszero,auxiliary) || return nothing') < hh.index('permuted=Vector{Float64}(undef,n);transformed=similar(permuted)'))
check('staged-selection', 'Scratch acquisition is STAGED' in spec and 'Only after that guard succeeds acquire permuted and transformed' in spec)
check('atomic-retention', 'atomically attach all four if eligible' in spec and 'never retains a partial pair' in spec)
check('early-native-order-preserved', 'No new later-buffer allocation can precede a native solve exception or the auxiliary guard' in spec)
check('conditional-allocation-ledger', 'only two length-n Float64 arrays (16*n payload)' in spec and 'requests four (32*n)' in spec and 'Cached paths make zero such requests' in spec)
check('early-exit-future-control', 'orientation_staged_early_exit' in plan and 'cold/nonretained orientation early exit' in plan and 'Distinguish synthetic from genuine backend tests' in plan)
check('feasible-normalization-rejection', 'normalization_rejection_first_middle_last_offdiagonal' in plan and 'finite nonzero D/D=1 cannot trigger' in spec)
check('failure-and-raw-contract-preserved', 'preserve active inner identity' in spec and 'no write to raw U.nzval' in spec and 'same CSC column/slot order' in spec)
check('memory-scope-preserved', 'A_old+A_new+E_t+W_t' in spec and 'NOT a proof of Julia header/allocator size' in spec and 'no second active factor' in spec)
check('scope-no-candidate', not (R / 'diagnostics/direct-bg-export-workspace').exists() and 'No Julia/query/parser/import/compile' in spec)
closure = read(E / 'closure-final.py')
publication = read(E / 'publication.py')
read(E / 'closure.py')
check('closure-uses-amendment', "rd(E/'amendment-review.json')" in closure and 'original_verify' in closure and "not matches and not unread and len(groups)==246" in closure)
check('publication-binds-closure-and-exact-files', "c['all_passed'] is True" in publication and 'closure bindings' in publication and 'exact stage names' in publication and 'final blobs' in publication)
read(Path(__file__).resolve())
result = {
    'scope': 'Independent amended planning review only; no Julia, old checker execution, host polling, candidate implementation or numerical measurement.',
    'accepted': all(checks.values()), 'findings': [],
    'critical': 0, 'important': 0, 'minor': 0,
    'all_passed': all(checks.values()), 'checks': checks,
    'resolved_initial_findings': ['R1', 'R2'],
    'readtime_sha256': bindings,
    'evidence_sha256': {p: digest for p, digest in bindings.items() if p.startswith(str(E) + '/')}
}
with (E / 'amendment-reviewer-check.json').open('x') as f:
    json.dump(result, f, indent=2)
    f.write('\n')
review = '''# Independent amendment review: direct BG export/import workspace

Accepted for planning only. Outstanding findings: 0 critical, 0 important, 0 minor. Initial review R1 and R2 are resolved; the original rejected review and exact before-documents remain preserved. This acceptance authorizes neither implementation nor numerical execution.

R1 is resolved by staged acquisition. On a missing group, work/auxiliary are acquired after the all-unit/scaling guards; permuted/transformed are acquired only after the original ldiv! and finite/nonzero auxiliary guard. This matches the frozen source's relevant order and prevents two additional arrays from being allocated on the early solve/fallback path. Retention is atomic after all four acquisitions, so the workspace never owns a partial pair. A complete cached group can supply the same arrays at those points without new requests. Early failure and fallback drop private scratch and preserve active factor ownership. The ledger now distinguishes two requests/16*n payload on the cold early path, four/32*n on the complete cold path, and zero on cached or all-unit paths; failed individual acquisitions must be counted at the actual failed position. Synthetic guard/allocation-failure controls and a separately bounded future cost control are explicit, and are not presented as real backend evidence.

The staged acquisition requirement makes work/auxiliary local scratch. I interpret original orientation arguments as the six numerical inputs F,L,U,p,q,scaling, with owner/n/l/u and allocate added; The binding Task1 interpretation is `_bgx_scale_mode(F,L,U,p,q,scaling,owner,n,l,u; allocate=_bgx_allocate)`; callers provide no preallocated work/auxiliary. This is consistent with the explicit prohibition on eager scratch acquisition.

R2 is resolved by first/middle/last eligible off-diagonal rejection fixtures. Validated literal CSC endpoints are diagonals and cannot fail finite nonzero D/D normalization. Separate malformed-export and diagonal-ineligibility tests retain their own intended boundaries. The original rejected slot, CSC order, signed-zero bits, unchanged raw U and full raw recovery remain required.

The broader conclusions of the preserved initial review stand. The proposed first scope is an honest partial response to reducing export/import overhead: bounded seen/orientation reuse and fused normalization into freshly owned packed U. Source supports removal of 8*u temporary payload and 2*u stores on successful normalization; it does not support an observed speedup or elimination of backend/extraction costs. Markowitz ignores HHExtractWorkspace, so unchanged raw extraction and that explicit deferral are appropriate. Full backend/spare-output reuse, other stopped candidates and import-reserve changes remain excluded.

Computational work and memory conclusion: no unnecessary NEW computational work, allocation or retained-memory cost remains identified in the amended design. The identified early-exit allocation increase has been removed by the staged requirement. Required guards, p/q reset passes, diagonal lookups, divisions and native conditional solve remain. Partial normalization can add overwrite work and is separately charged. Wrapper forwarding adds no prescribed per-RHS scans, solves or copies. Private scratch is dimension/budget checked, exact length, atomically retained, released on failure/fallback, and absent in copies. The policy charge is expressly not an allocator/graph/native-memory bound; the complete wrapper/workspace graph, old plus new factors, extraction/backend temporaries, updates, caches and copies remain part of future measurement. Runtime liveness and physical peak savings remain unproved.

Future validation is sufficient as a planning requirement: exact-stage source inversion, all seven original fixtures and both selected policies, every relevant failure/publication boundary, scratch poisoning, copy divergence, core permutations, signed zeros, source input bits, direction provenance, shrink/budget transitions and new feasible early/late controls. The sparse/dense paired schedule includes all lifecycle work, allocation events and bytes, compilation controls and intermediate/final graph gates. Separate ordinary-BG qualification, longer histories, other precisions and public routing remain necessary before production consideration. Documentation changes need no numerical benchmark now.

The new amendment-reviewer-check.py was saved before its single execution. It independently verifies every original author binding against the exact before-doc mapping, every initial reviewer binding/evidence hash, every amendment-author binding, and all eight selected frozen source files against the original sealed inventory. Current amended documents, unchanged source and preserved evidence are bound directly in this review's readtime_sha256. The original and amendment author checkers were read but not run or imported. No Julia, host polling, implementation, compile, numeric test or old evidence rewrite occurred.

Read and bound closure-final.py and publication.py as UNEXECUTED prospective scripts, together with the original UNEXECUTED closure.py draft. The canonical closure selects the accepted amendment review, maps original document hashes to before-files, checks exact names/refs/current hashes and fresh host conditions; publication gates on closure and exact staged blobs. Actual closure, staging, commit and push outcomes remain the parent's responsibility and are not certified here. Future Julia syntax/loadability, runtime work counts, numerical equivalence, GC/allocator effects, native retention and physical peaks are likewise not certified by a document review.
'''
with (E / 'amendment-review.md').open('x') as f:
    f.write(review)
result['evidence_sha256'][str(E / 'amendment-reviewer-check.json')] = hashlib.sha256((E / 'amendment-reviewer-check.json').read_bytes()).hexdigest()
result['evidence_sha256'][str(E / 'amendment-review.md')] = hashlib.sha256((E / 'amendment-review.md').read_bytes()).hexdigest()
with (E / 'amendment-review.json').open('x') as f:
    json.dump(result, f, indent=2)
    f.write('\n')
print(json.dumps({'all_passed': all(checks.values()), 'checks': len(checks), 'bindings': len(bindings), 'accepted': result['accepted'], 'critical': 0, 'important': 0, 'minor': 0}))
if not all(checks.values()):
    raise SystemExit(1)
