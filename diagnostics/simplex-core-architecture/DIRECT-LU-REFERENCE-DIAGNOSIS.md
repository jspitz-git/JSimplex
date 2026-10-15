# Direct LU reference residual: source and saved-evidence diagnosis

The first failed DSE output is localized to the ordinary native backend boundary,
by source reconstruction of the admitted call sequence. It is not evidence of a
fault in the direct-LU candidate. The native factor representation/application
cause remains unobserved. Task 3 cost1 stays failed and consumed; cost2 is blocked.
No Julia, parser, import, factorization, solve, native call or old auditor was run.

## Why the wrapper cannot explain the first failure under this source path

The loaded ordinary factorization, triangular_factorization, triangular_rows and
triangular_spikes files match the production source byte for byte and their launch
pins. The driver creates 24 distinct zero vectors, never passes DSE outputs as
replacement directions, and retains each as a detached output. Prepared-spike
entries retain destination references but write only owned direction/spike buffers;
replacement reads its entering direction, not the DSE output. Later eviction and
refactor invalidate references rather than mutating returned output vectors.

The fourth update is followed by _refactorize_triangular!. The first native
refactor has no spare, so _refactorize_backend calls fresh lu(B4), not lu! or
symbolic reuse. It publishes this backend, resets upper to identity, both column
maps to 1:n, clears active update history, resets compiled row operations/order,
clears active-upper entries and invalidates prepared provenance. No copy, sharing,
sparse route or direct exporter is entered in this reference sequence.

At step 5 the entering FTRAN changes only scratch/prepared metadata. No replacement
occurs until AFTER DSE FTRAN. Consequently both solves still see the empty history,
identity maps and no active upper columns. In the applicable triangular_rows.jl
_finish_triangular_forward! specialization, the post-backend action is an identity
copy into work and back plus prepared-buffer copies. There is no arithmetic on the
output. Thus the saved step-5 DSE values are source-derived equal to the result
returned by ldiv! on the fresh UMFPACK factor of B4. This is a source-supported
boundary inference, not a captured internal callback or native-factor snapshot.
Steps 6–8 do have update arithmetic and are not claimed to be identity wrappers.

The installed wrapper allocates fresh controls, copies controls into each factor,
and explicitly defaults IRSTEP to zero. The ordinary backend calls ldiv! directly;
it does not request extra refinement. The private exporter does not write these
controls. This rules out a source-supported global-control leakage explanation,
not arbitrary hidden native state. Enabling refinement or changing pivot controls
would change the experiment and is NOT an accepted fix.

## New exact facts from saved values

For all eight reached sparse96 DSE matrices, each row has a unique dominant value
4, and the dominant columns form a permutation. After undoing that column
permutation the strict row diagonal-dominance margin is at least 103/32 and the
infinity norm is at most 153/32. The elementary dominance bound gives
||B^-1||inf <= 32/103 and kappa_inf(B) <= 153/103 = 1.4854368933.
Row/column permutations preserve these infinity norms. This is a bound, not an
estimated condition number from a numerical solver. Ill-conditioning of this
matrix is therefore not a sufficient explanation for the observed residual.

All eight DSE RHS token vectors are identical. At the first failure (step 5), row
87 reads (1/4)*x6 + 4*x7 - (1/2)*x8 = 29/32. The saved values give the exact positive
residual 9928545/144115188075855872. The fixed bound is
144694209253234815/39614081257132168796771975168, ratio 18.861415966018026.
This row and these three solution tokens are unchanged in steps 5–8, explaining
why their maximum residual is identical. It does not prove identical full outputs.
The full exact residual vectors, norms and row terms are in analysis.json.

Native factors, permutations/scales, controls, condition/growth information and
base-only output were not captured. We cannot separate LU representation error
from solve application error, prove the native pivoting cause, or establish
reproducibility from this single run. No source repair is justified yet.

## Evidence and verification limits

New analyze.py was saved and executed once: 17/18 gates passed. The last gate
incorrectly compared a hash string with a structured inventory record. Its false
result and script are preserved. A separate four-gate pin-supplement checks the
actual sha256/resolved fields for all 15 selected source paths, confirms the
unchanged original bindings, and passes without repeating the arithmetic. All
15 paths were already launch-pinned; no retroactive launch pins were introduced.
Initial nonexistent path selectors and a bytecode-cleanup allowlist refusal are
recorded in entry-notes.json. Only self-created control.cpython-314.pyc was removed.
Fresh host identity covers all 204 groups AND sessions, no Julia, HEAD ea82a59,
master 6f68e24. Before-diagnosis continuation copies preserve exact prior bytes.

No production change, hence no new production scans, allocations or retained
memory. The Python exact row traversals and saved-data hashes are diagnostic work.
The next plan charges all diagnostic solves/copies separately; it does not promise
performance gains or remove safeguards. Earlier n32 candidate cost rejections,
known duplicate harness scans/retention and all failed evidence remain unchanged.

## Next bounded step

Prepare the separate driver/admission described in
2026-10-15-direct-lu-reference-backend-diagnostic.md and independently review it.
Do not execute that future process under this source-only step. A new immutable
stage admission is required. One diagnostic process, not a benchmark rerun, can
compare fresh B4 backend with the original prefix followed by refactor, capture
raw native factors and separate representation/application explanations. No new
candidate or tolerance, control, precision, fixture or production changes.
