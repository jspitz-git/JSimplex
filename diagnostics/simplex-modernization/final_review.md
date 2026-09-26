# Whole-branch review and corrective validation

Status: two Important findings reproduced and fixed; fresh native production,
development, GLPK and external quick-corpus validation passed.
No integration or push has occurred.

One independent fresh-context review covered `d93cfd3..620f778`. It reported no
Critical or Minor findings and two Important findings. The reviewer also checked
150 small bounded LPs against vertex enumeration with both adaptive algorithms
(300 successful solves). That targeted review evidence supplements the test
suite; it does not replace it.

## Auxiliary-to-original handoff

The existing handoff published the auxiliary basis into the original workspace
before rebuilding its factor. A logger exception at the rebuild left the live
basis and factor inconsistent. For `min -x` with `x >= 0` and row upper bound 1,
the live basis changed from the slack column -1 to structural column 1 while the
factor still represented -1. A subsequent solve through that factor failed to
solve the advertised basis. The same boundary also admitted stop-callback and
deadline interruptions after partial publication.

The handoff now uses private staged values, a copied factor and independently
owned refactor-policy state. It recomputes original-bound values and verifies
finite dual feasibility before publication. All caller code runs outside the
publication window; consumed auxiliary steps and completed refactor work remain
counted on interruption. Tests check forward and transposed basis consistency,
unchanged live values, exception identity and successful resumption, with the
optional Phase I policy both off and on.

The initial regression changed from 50 passing / 22 failing checks to 72/72
passing checks. An expanded check then found that publication could restore a
stale rejected-pivot list from the trial after invalidating the live list. The
private trial now invalidates its phase caches before reconstruction as well.
That regression failed three checks, then the expanded suite passed 78/78
with `--compile=min`. The initial native full-suite run was deliberately stopped
before completion to include this correction; its logs are preserved and it is
not counted as a passing gate. The subsequent fresh native full suite passed.

## Stored BigFloat precision at public entry

Automatic numerical-policy construction used ambient `eps(BigFloat)` before
starting the solver. A model and options built at 256 bits therefore raised an
`ArgumentError` when solved under an 8-bit ambient context, even in legacy mode;
the original baseline solved the small reproducer.

Automatic policy construction now uses a local precision scope covering the
maximum stored model and option precision and the ambient precision. Ordinary
solve arithmetic retains its documented ambient precision; explicit standalone
construction of an insufficient-precision policy still raises an error.
Tests exercise public primal and dual solves under both strategies, with zero
and one row, while checking that ambient precision and stored inputs remain
unchanged.

The regression first failed all eight solve-entry checks (25 pass / 8 fail),
then passed 57/57 checks with `--compile=min`, followed by the passing native
full suite.

## Fresh verification after both fixes

The final production fingerprint is
`b38a8a2f5c6e69515ee55d740f3846c76f285f56868ff521f02bf2858d069cf8`.
The source and test inventory remained frozen throughout the sequential gates:

- Production: 253,747/253,747 checks, 117 minutes 41.2 seconds; fresh native run.
- Development: 1,208/1,208 checks across 69 testsets, including 249 JET checks.
- Numerical comparison with GLPK: 6/6 cases passed.
- Focused handoff, driver, recovery, Phase I and policy integration:
  1,423/1,423 checks with `--compile=min`.

The [verification record](final-verification.json) records counts, source identity
and log hashes. The connection interruption did not stop the local gates; their
completed logs and zero exit codes were recovered without repeating them.

The post-review [quick-corpus results](final-quick.json) contain 224 measured
optimal solves: eight external cases, primal and dual methods, legacy and
adaptive strategies, and seven samples per combination. Each method had two
fresh warmups. Every measured result passed original-unit primal feasibility
checks and matched an accepted reference objective on the hash-matched input.
The cases were afiro, adlittle, kb2, sc50a, pk1, flugpl, stein9inf and
markshare_4_0; MIP cases were explicit LP relaxations. Runs were sequential with
diagnostics disabled, a 60-second solve limit and a 24-GiB requested memory cap.
These are correctness observations, not evidence of a general speed improvement.
The source revision field identifies the pre-fix parent; the recorded source
fingerprint above identifies the exact tested working sources.

## Evidence boundaries and retained decisions

The F25 corpus records remain unchanged historical observations of production
fingerprint `cc14d2e38ae5a9fa8cdddb40665f60f3fac30adb9280481b073060085814b824`.
They are not relabelled as measurements of these fixes. Source changes invalidate
the previous production-suite reuse, so the complete native production suite was
rerun, followed sequentially by the complete development/JET/JuMP checks
and numerical GLPK comparisons. The fixes do not justify promoting adaptive
policies or claiming a performance improvement.

The review set aside the pre-existing blend parser failure and wholesale changes
to scaled-unit tolerance semantics. Both decisions and their limitations remain
in the [decision record](decisions.md). There are no deferred minor findings.
The branch, worktree and local validation evidence are retained.
