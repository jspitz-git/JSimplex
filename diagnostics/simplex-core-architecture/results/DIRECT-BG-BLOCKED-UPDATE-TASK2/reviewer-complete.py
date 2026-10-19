from pathlib import Path
import json,hashlib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');C=R/'diagnostics/direct-bg-blocked-update/reproduce';Q=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-TASK2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
first=json.loads((Q/'review-first.json').read_text());fresh=json.loads((Q/'reviewer-final-check.json').read_text());fix=json.loads((Q/'review-fix.json').read_text());binding=json.loads((Q/'reviewer-final-binding.json').read_text())
checks={}
checks['twenty_five_source_checks_passed']=len(fresh['checks'])==26 and all(v for k,v in fresh['checks'].items() if k!='corrected_binding')
checks['all_current_candidate_bytes_match_fresh_review']=len(fresh['sha256'])==14 and all(sha(R/p)==h for p,h in fresh['sha256'].items())
checks['initial_bindings_exact_named_versions']=all(sha(R/fresh['initial_binding_resolution'].get(p,p))==h for p,h in first['sha256'].items())
checks['fix_bindings_exact_named_versions']=all(sha(Path(binding['fix_binding_resolution'].get(p,p)))==h for p,h in fix['sha256'].items())
checks['other_seven_followup_checks_passed']=len(binding['checks'])==8 and all(v for k,v in binding['checks'].items() if k!='all_prior_reviewed_candidate_bytes_accounted')
checks['current_report_unchanged']=sha(Q/'REPORT.md')==fix['sha256'][str(Q/'REPORT.md')]
assert all(checks.values()),checks
with (Q/'reviewer-completion-check.json').open('x') as f:json.dump(dict(all_passed=True,checks=checks,scope='Final exact binding checks; no numerical execution'),f,indent=2);f.write('\n')
report='''# Independent Task2 source review — accepted offline preparation

Accepted after the single bounded R1–R5 correction pass. No outstanding source-review findings. This receipt covers the exact candidate/test/fixture/manifest/ledger/report bytes in review.json. **Runtime acceptance is false.** No Julia executable, query, parser, import, compiler, numerical calculation, test or benchmark was run. No old checker was executed. No production, candidate, frozen Task1 or Git state was changed by the reviewer.

## Corrections verified

R1: Scalar observation and both packed argument reads are now inside `probe!==nothing`. The unobserved scalar route no longer requires two extra binary searches per ordinary pivot at source level. Its inverse still matches the original scalar arithmetic and pivot policy after removal of the guarded observation.

R2: Panel-boundary dispatch now checks the exact current diagonal once. A zero diagonal goes directly to the original scalar suffix, whose full pure-run lookahead occurs once. This preserves the unrestricted pure-run algorithm and removes the duplicated potentially long scan. The remaining boundary lookup is O(log(nnz(column)+1)); the ledger now includes the packed-search factor in full-run complexity. No tolerance, coefficient dropping or frozen-kernel change was introduced.

R3: The no-elimination lifecycle test selects the original column identity through `f.inner.column_order[end]`, asserts its final packed position, and uses that identity for both B-column extraction and replacement. It no longer assumes a backend permutation.

R4: The ledger uses11488 bytes at n96 and five successful lifecycle FTRAN entries per backend, with busy attempts separate. It includes12 synthetic-H constructors/elimination entries after R5 and explicitly charges256 temporary cold reference wrappers across the numerical roster. These wrappers are not the proposed timed reference route. The132? count is not used: the frozen roster remains13 streams,128 replacements per backend per side,52 factor constructors,512 replacements,1536 FTRAN and512 BTRAN entries in the numerical tests alone. Lifecycle and rejected attempts remain additional.

R5: A new cold failure test arms writeback at the second panel boundary, requires two starts and exactly one previous completed panel, checks original exception identity and one fault hit, forbids finish/final-update publication and asserts conservative cache/scratch/busy cleanup. Partial U mutation is permitted, as in the specified failure contract. The three original first-panel fault tests remain.

## Numerical and lifecycle assessment

The original prepare-spike/tolerance/provenance path, begin/finish discipline, incidence replacement, column rotation and spike clearing remain intact. The corrected scalar suffix is an exact textual inverse of the original with declared type/namespace/start substitutions and two cold events. Private panel rejection resumes from its unchanged boundary and prevents further blocking; nonfinite rejection leaves candidate prefix eligibility false. Committed panel steps are appended chronologically, and only one whole-update record is published after complete elimination. Failure drops wrapper scratch, invalidates prepared/upper/incidence state, clears both prefix flags and resets busy without claiming rollback. Copies have no shared wrapper workspace; same-size refactor may retain it and any dimension change drops it.

The unchanged tests use independent original-B column replacements and exact rational residuals at the frozen128*n*2^-52 bound. H is captured after spike insertion/column rotation and before elimination. Independent chronological elementary transformations are compared with stored history, H-to-U relation and floating shadow U; original-B solves prevent a matching but wrong U/history pair from certifying itself. Base/lower/scaling/permutation data, input snapshots, incidence and copy ownership are checked. Negative zero/nonfinite microcases avoid the positive finite Trace pivot assertion. Input stress names remain recipes, not proof of a particular backend pivot trajectory. Runtime dispatch and the actual numerical coverage still require separate admission.

No obvious Julia syntax defect was found by inspection. This is not a parser or compiler claim. The previously identified no-op test and hot-path work defects are resolved; no further definite source correctness defect was established.

## Computational work and memory verdict

The two unnecessary NEW lookup costs found in the first review have been removed from the corrected source. **No remaining unnecessary new work or retained-memory owner was established by this review.** The chosen design still adds work and retained scratch, and no speedup is inferred.

Construction uses ordinary factorization/export/import plus one wrapper. Ordinary forwarding adds no basis solve, input conversion/copy or full-vector scan. Each replacement retains the original provenance/fallback spike work, incidence maintenance, spike clearing and history ownership. Panel admission performs a boundary diagonal lookup plus separate eligibility/gather traversals. Gather initializes the active values/masks; first use initializes the full n-by9 allocation. Chronological arithmetic uses the frozen bounded FMA/swap/finite-check loops. Commit repeats support searches, guards explicit packed stores by2*h*w before fresh-column allocation, reserves h incidence rows, and rebuilds those rows in one ascending n-ID pass. Lookup work across panels scales O(n² log n/8), with fixed-block tile/commit work O(n²). Sparse rejection adds a band traversal; private rejection can repeat up to eight attempted steps through the scalar suffix. No per-panel basis solve or uncapped cubic packed rewrite appears.

One optional owned workspace has checked logical charge72n+16*cld(9n,64)+4352, at most308480 bytes for n4096. This excludes actual allocator capacity, GC/native storage and original factor/history caches. Sequential changed-column old/new coexistence and delayed collection remain additional. No second persistent tile, full-factor copy, per-pivot vector or hot growing trace is introduced. Cold Trace snapshots, exact rational O(n³) relation work, Test objects and temporary reference wrappers are explicitly additional and untimed. No300s-fit, allocation equivalence, compiler-elimination or before/after timing claim is accepted. Later sparse/dense matched whole-lifecycle measurement remains mandatory.

## Exact evidence and preserved checker history

Fresh reviewer-final-check.py verified25 source/hash/inverse conditions, including full14-file candidate membership, corrected scalar/fault inverses, original/staged pins, include inverse, frozen Task1/fixtures/numerical tests and tests-first preserved versions. Its one failed check compared the expanded ledger to the earlier review-fix.json hash; the author had added the cold-wrapper accounting paragraph and preserved the exact previous ledger. No executable candidate changed.

The next new reviewer-final-binding.py correctly established the explicit old fix binding and additive paragraph, but incorrectly tried to map the fresh check's already-current ledger hash to that old version. That reviewer-only failed check and source remain preserved. reviewer-completion-check.json resolves this with six passing checks: the fresh check's14 hashes match current files directly; the initial rejection resolves changes only through its six explicitly named `.before-review` files; the fix receipt resolves its ledger only through `.before-cold-budget`; the other25 source checks and seven follow-up checks hold; the report remains exact. No wildcard/any-matching-blob resolution is used. The current ledger hash is3a30781b0d912d56ccec27b9c5a6a24d67a6595b86325e0ad278feec9eee8b5a.

review.json binds all14 candidate-directory files, current report, complete existing Task2 reviewer/author/preserved evidence, consulted original sources, plan/spec and first-review dependencies. Both rejection and all unsuccessful author/reviewer check evidence remain intact.

## Boundary

Accepted only as offline candidate/test preparation. Driver/admission preparation is a separate later task; no runtime, numerical, performance, whole-solver or production integration acceptance is granted. Actual assertion counts, positive route coverage, failure prefixes, backend work budget, world-age/dispatch, original-B residuals, allocation/native/GC graphs and all timing gates remain to be demonstrated under that separately reviewed admission.
'''.replace('The132? count is not used: the frozen roster remains','The frozen roster remains')
with (Q/'review.md').open('x') as f:f.write(report)
paths={str(p.relative_to(R)) for p in C.iterdir() if p.is_file()}
paths.update(str(p.relative_to(R)) for p in Q.iterdir() if p.is_file() and p.name!='review.json')
paths.update(p for p in first['sha256'] if not p.startswith(str(C.relative_to(R))) and not p.startswith(str(Q.relative_to(R))))
result=dict(accepted=True,findings=[],resolved_findings=['R1','R2','R3','R4','R5'],runtime_acceptance=False,numerical_acceptance=False,performance_acceptance=False,scope='OFFLINE Task2 source preparation only',candidate_membership=sorted(p.name for p in C.iterdir() if p.is_file()),unnecessary_new_work_found_in_current=False,unnecessary_retained_memory_found_in_current=False,initial_binding_resolution=fresh['initial_binding_resolution'],fix_binding_resolution=binding['fix_binding_resolution'],sha256={p:sha(R/p) for p in sorted(paths)})
with (Q/'review.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print('Accepted offline source only; runtime_acceptance=false; '+str(len(paths))+' exact SHA256 bindings')
