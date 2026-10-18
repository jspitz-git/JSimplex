from pathlib import Path
import hashlib
import json

R = Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
E = R / 'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-WORKSPACE-PLAN'
bindings = {}
checks = {}
def read(path):
    p = Path(path)
    raw = p.read_bytes()
    bindings[str(p)] = hashlib.sha256(raw).hexdigest()
    return raw.decode()
def check(name, value):
    checks[name] = bool(value)

author = json.loads(read(E / 'author-check.json'))
texts = {}
for path, digest in author['readtime_sha256'].items():
    texts[path] = read(path)
    check('author_binding:' + path, bindings[path] == digest)
check('author_binding_count', len(author['readtime_sha256']) == 28)
check('author_reported_41_checks', len(author['checks']) == 41 and all(author['checks'].values()))
read(Path(__file__).resolve())
sealpath = R / 'diagnostics/simplex-core-architecture/results/DIRECT-LU-POLICY-ADAPTER-COST-PREPARATION/runs/cost1-300/sealed.json'
seal = json.loads(texts[str(sealpath)])
stage = R / '.superpowers/sdd/2026-10-16-direct-lu-policy-adapters/driver-stages/green/src'
for name in ('direct-factor.jl', 'factor-export.jl', 'huangfu_hall_factorization.jl', 'markowitz_factorization.jl', 'triangular_factorization.jl', 'triangular_indices.jl', 'triangular_rows.jl', 'bartels_golub_rows.jl'):
    p = stage / name
    check('sealed:' + name, bindings[str(p)] == seal['inventory'][str(p)]['sha256'] and str(p.resolve()) == seal['inventory'][str(p)]['resolved'])
S = R / 'docs/superpowers/specs/2026-10-18-direct-bg-export-workspace.md'
P = R / 'docs/superpowers/plans/2026-10-18-direct-bg-export-workspace.md'
spec, plan = texts[str(S)], texts[str(P)]
direct = texts[str(stage / 'direct-factor.jl')]
export = texts[str(stage / 'factor-export.jl')]
hh = texts[str(stage / 'huangfu_hall_factorization.jl')]
check('historical_triangular_difference', bindings[str(stage / 'triangular_factorization.jl')] != bindings[str(R / 'src/triangular_factorization.jl')] and 'differs from that historical stage' in spec)
check('reference_normalization_buffer_and_writeback', 'values=similar(U.nzval)' in direct and 'values[slot]=value' in direct and 'copyto!(U.nzval,values)' in direct)
check('reference_packed_copy', 'copy(@view U.nzval[nzrange(U,j)])' in direct)
check('reference_orientation_early_exit_precedes_last_two_buffers', hh.index('ldiv!(auxiliary,F,work)') < hh.index('all(isfinite,auxiliary) && any(!iszero,auxiliary) || return nothing') < hh.index('permuted=Vector{Float64}(undef,n);transformed=similar(permuted)'))
check('reference_diagonal_finite_nonzero', 'isfinite(D[col]) && !iszero(D[col]) || return nothing' in direct)
check('reference_upper_order_and_diagonal_required', 'previous<row<=n' in export and '(lower ? row>=col : row<=col)' in export and 'diagonal || throw' in export)
check('raw_extraction_unchanged_contract', 'Extraction still uses fresh HHExtractWorkspace' in spec and 'unchanged raw extraction' in plan)
check('markowitz_extract_ignores_workspace', 'function _hh_extract_parts(F::MarkowitzBackend{T},::HHExtractWorkspace)' in hh)
check('no_candidate_created', not (R / 'diagnostics/direct-bg-export-workspace').exists())
check('policy_charge_distinguished_from_graph', 'NOT a proof of Julia header/allocator size' in spec and 'A_old+A_new+E_t+W_t' in spec)
check('production_comparison_separate', 'separately admitted matched comparison to ordinary BG is mandatory' in spec)

findings = [
    {
        'id': 'R1', 'severity': 'important',
        'title': 'Specify and charge orientation acquisition before the native early-exit guard',
        'file': str(S), 'line': 55,
        'related_locations': [str(S) + ':53', str(S) + ':73', str(P) + ':40', str(stage / 'huangfu_hall_factorization.jl') + ':176'],
        'body': 'The planned all-or-none four-buffer acquisition and explicit four-buffer helper inputs move permuted/transformed allocation ahead of the native solve and its finite/nonzero auxiliary guard. The frozen helper allocates those last two vectors only after the guard. On a cold or nonretained call that throws in ldiv! or returns nothing at that guard, the eager design can request two unnecessary length-n Float64 arrays (16*n payload bytes plus headers), and a new allocation failure can precede the original solve failure. The current ledger records the conditional solve but not this conditional allocation increase; the explicit allocation-order exception describes final packed output only. This leaves a material failure-path work/exception-order decision to implementation.',
        'requested_change': 'Select eager or staged acquisition explicitly. If eager, charge the two extra early-exit array requests/payload and explicitly state the allocation-failure ordering allowance while preserving numeric fallback and active ownership. If staged, specify how staged transient acquisition and atomic all-or-none retention work. Add future early-orientation-failure/fallback allocation/ownership controls and bind their work in the later concrete admission. No numerical run is needed for this planning correction.'
    },
    {
        'id': 'R2', 'severity': 'minor',
        'title': 'Define first and last rejection positions as eligible off-diagonal slots',
        'file': str(P), 'line': 42,
        'related_locations': [str(P) + ':25', str(stage / 'factor-export.jl') + ':24', str(stage / 'direct-factor.jl') + ':83'],
        'body': 'Taken literally, normalization rejection at the first or last slot of valid upper CSC is impossible. Sorted triangular storage with required nonzero finite diagonals starts with U[1,1] and ends with U[n,n]; both divide by their identical diagonal and produce exactly 1. The requested first/middle/last rejection tests need feasible positions to avoid malformed factors or assertions that cannot fail through the intended safeguard.',
        'requested_change': 'Define these as first/middle/last eligible off-diagonal division positions (early/interior/late rejection), and keep diagonal-ineligibility and malformed-export tests separate. Require the same rejected CSC index and original traversal order.'
    }
]
result = {
    'scope': 'Independent planning-only offline review; no Julia, old checker rerun, host polling, implementation, numerical tests or performance measurement.',
    'integrity_checks_passed': all(checks.values()),
    'checks': checks,
    'accepted': False,
    'findings': findings,
    'counts': {'critical': 0, 'important': 1, 'minor': 1},
    'readtime_sha256': bindings,
    'evidence_sha256': {str(E / n): bindings[str(E / n)] for n in ('host.json', 'author-check.py', 'author-check.json')}
}
with (E / 'reviewer-check.json').open('x') as f:
    json.dump(result, f, indent=2)
    f.write('\n')
review = '''# Independent direct BG export/import workspace plan review

Changes requested before planning acceptance: 0 critical, 1 important, 1 minor. This is the initial review; preserve it and its exact input bindings if the author amends the documents. No implementation or numerical execution is authorized by this review.

R1 (important), spec lines53/55/73 and plan line40: explicitly settle orientation scratch acquisition on the native early-exit path. The frozen HH helper calls ldiv! at line176, rejects nonfinite/all-zero auxiliary at line177, and only then allocates permuted/transformed at line180. Supplying an all-or-none four-vector group up front adds two length-n Float64 requests on cold/nonretained early failures or fallbacks: 16*n payload bytes plus headers. An allocation exception can also happen before the native solve exception. The spec acknowledges allocation-order changes for final packed output, but does not state this orientation case or charge it in its work ledger. Either document eager acquisition and these costs/error-order limits, or specify staged acquisition followed by atomic retention. Add a bounded future control for the early orientation exit and acquisition failure, without running numerics now.

R2 (minor), plan lines25/42: clarify first/middle/last normalization rejection as first/middle/last eligible off-diagonal slots. For a validated upper CSC, its first and last stored coefficients are finite nonzero diagonals and divide by themselves to exactly 1. Literal endpoint rejection is impossible. Diagonal-ineligibility and malformed-CSC tests should remain separate; preserve the same actual rejected CSC position and arithmetic order.

The selected partial scope otherwise meets the request for a reusable private export/import workspace with a source-informed budget. It openly defers whole backend reuse, CSR/triplet extraction reuse, spare full factors, dynamic/block/split candidates and import-reserve changes. Markowitz ignores HHExtractWorkspace, so retaining that extraction object alone would not address its costs. Successful normalization is a credible independent mechanism on both backends: reference direct-factor.jl creates a length-u temporary, writes u normalized values, copies u values back to CSC and then copies u into packed columns. Writing directly to final packed values removes 8*u temporary payload and 2*u stores without removing divisions, finite/underflow checks, D or the original raw CSC. This is a source count, not measured allocation events or a speedup.

Ownership and numerical contracts are otherwise adequate for this planning stage. Complete private replacement plus concrete type check precedes publication; failure drops private cache without modifying active state or saved factors. Copies begin without workspace and retain the original inner copy/sharing contract. Busy/reentrant refactor/copy rejection is explicit. Fused import preserves CSC traversal, row-index copies, original D lookup order, signed zeros and exact raw recovery after rejected division. Raw extraction, both triangle checks, p/q resets, scale checks, native orientation arithmetic and conditional real solve remain mandatory. Future tests include each allocation seam, copy/refactor divergence, poisoned scratch, Markowitz core permutations, provenance, aliases and same-n smaller-nnz budgets. The original inner copy mutates shared_update_count as part of its existing copy contract; the plan must continue to preserve that original contract rather than assume copying is field-pure.

Computational work and memory conclusion: I found one avoidable/unbudgeted NEW allocation case, R1. Apart from that case, no unnecessary new full-vector scan, basis solve, conversion or per-iteration allocation is prescribed. The proposal limits new checked budget decisions to setup/refactor, reuses exact-length scratch, and forbids new solve/update scans. Normalization rejection can incur partial normalized stores plus a raw refill and is explicitly charged. Fresh backend/extraction/final output and full replacement remain deliberately in scope as existing costs. Thus expected savings are partial and can fail all-cell performance gates.

The charge cap is an admission policy, not a claim about allocator headers or native memory. P0=16*(l+u)+8*(n+1) is a valid lower bound on live Float64/Int lower-plus-packed-upper payload, omitting extra dimension structures and all headers. A workspace charge of 512 plus BitVector chunks and four Float64 vectors is explicitly distinguished from actual reachable graph. Dimension/budget shrink, exact lengths, no partial attachment, failure release, no high-water capacity credit and no extra retained backend/factor are sound requirements. Old/new factor graphs, extraction/backend temporaries, retained and transient scratch, update history, caches and copies are all acknowledged in coexistence accounting; physical peaks and native frees remain unproved. Future graph gates include the wrapper and workspace rather than only coefficients.

Validation performed: the NEW reviewer-check.py was saved before execution. It independently rehashed all28 author read-time bindings and matched all eight selected frozen numerical source files to the sealed inventory (hash and resolved path). It confirms the documented live/historical triangular_factorization.jl difference, original normalization/copy source, orientation guard order, ignored Markowitz workspace, absence of a candidate and preservation of separate ordinary-BG comparison. The author's checker was read, never imported or rerun. The exact docs, sources, author script/result, host evidence and this new script are bound in reviewer-check.json and review.json. Hash integrity is distinct from the semantic findings above.

The future task split is appropriate: offline implementation/test text first, exact-stage independent admission before any RED/GREEN or cost run, and no assumed inherited RED count. The primary sparse/dense paired schedule includes construction/export/import/refactors and wrapper costs, retains GC/outliers, separates phase medians, requires all eight cells and intermediate/final graph gates, and requires a separate ordinary-BG comparison before production consideration. Extend those future concrete controls for R1. Float64/Int scope is explicit; other precisions and public integration remain unqualified. No benchmark is required for the present documentation review. I did not validate future Julia syntax, numeric outputs, exact allocations, physical peaks, runtime/native work, host admission freshness or publication state.
'''
with (E / 'review.md').open('x') as f:
    f.write(review)
result['evidence_sha256'][str(E / 'reviewer-check.py')] = bindings[str(Path(__file__).resolve())]
result['evidence_sha256'][str(E / 'reviewer-check.json')] = hashlib.sha256((E / 'reviewer-check.json').read_bytes()).hexdigest()
result['evidence_sha256'][str(E / 'review.md')] = hashlib.sha256((E / 'review.md').read_bytes()).hexdigest()
with (E / 'review.json').open('x') as f:
    json.dump(result, f, indent=2)
    f.write('\n')
print(json.dumps({'integrity_checks_passed': all(checks.values()), 'checks': len(checks), 'bindings': len(bindings), 'accepted': False, 'counts': result['counts']}))
if not all(checks.values()):
    raise SystemExit(1)
