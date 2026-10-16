# Direct LU policy adapter — offline candidate and test preparation

Task1 of the accepted 2026-10-16 direct LU policy adapter plan. Source preparation
only; no Julia query/parser/import/compilation/test/numerical execution. No runtime,
RED/GREEN, allocation or speedup acceptance. Actual master26e2291745999f485a74f643298ca997d65c7205
and diagnostic a3fec9a0d89bf687c2ac6b2ef6ddc771e6032491 are distinct source baselines.

## Implementation and inverse

New files live only in diagnostics/direct-lu-policy-adapters/reproduce. The common
factor export and seven-fixture/oracle source are byte-identical copies of frozen
historical inputs. direct-factor.jl has exactly eight textual edits, with a whole
source inverse in candidate-inverse.json: immutable enum field, copy forwarding,
Float64 factory signature/test-only keyword, pre-work Markowitz rejection and one
policy-aware backend call, two constructor argument sites, default compatibility
and generic forwarding block, stored-policy refactor forwarding. All solve/update,
normalization, packing and manager initialization bodies remain byte-identical.
No factory/control object is retained by the adapter. No actual src/test/Project,
environment, CI or master change. Other supported precisions delegate ordinary
Factor(B,backend,policy), including pre-work Markowitz nondefault rejection.

## Tests prepared, not executed

Tests were saved before candidate creation; tests-before-candidate.json binds that
state. The subsequent explicit test revision extends real export identity coverage
to native threshold_one too; its original hash maps only to
lifecycle-tests.before-export-policy.jl. No original test/evidence was rewritten.

red.jl contains seven structural missing-contract checks against a NEW old-adapter
on current-master overlay (six applicable checks plus one field check), zero factor
calls. It has not demonstrated failure. lifecycle-tests.jl adapts the historical
corrected suite, retaining exact Float64-token residual bounds, seven input
fixtures, eight replacements, DSE interference, copies/divergence, singular
transactionality, successful resize, indexed/aliased solves and BG row order.
126 paired setups cover7fixtures×3managers×3validarms×2normalization requests.
Real export identity tests cover21 fixture/arm combinations; synthetic malformed,
scaling and normalization rejection cases remain. Historical19557 PASS is not
claimed for new source or used as an expected assertion count.

policy-tests.jl adds18 transition sequences (3managers×3arms×2normalization), each
8 successful real backend/export entries plus1 singular construction attempt.
Eight observed entries include an injected post-export exception. Each sequence
covers empty→nonempty, copy, resize, singular failure, direct→fallback, fallback
copy, exporter failure, direct, empty and nonempty; copied old states remain usable.
Native observations include2 empty/6 nonempty entries, with actual20control values
checked before export, plus actual strategy observation (last observation retained,
not a complete native trajectory). Markowitz has8 real export entries. The
unavailable-export seam runs AFTER real factorization; the throwing factorize seam
is used only for early rejection and never stored. Legacy-forwarder tests add
24 constructions. Float64 rejected-policy checks have12 requests with zero
prospective factory/export calls; invalid manager/backend add2 rejection requests.
Generic tests add45 ordinary constructions,27 copied-factor refactors,18 rejected
requests across Float32/BigFloat256/Rational{BigInt}, with exact dyadic solution and
input/container/scalar-owner checks. Generic zero-work rejection is source-supported,
not runtime call counting. Exact dynamic Test assertion tree and all helper solves,
copy/export/oracle/internal-orientation work must be frozen in later Task2 admission.
These entry counts are not a complete backend/PREforward budget.

## Work and memory review

Only constant-size policy metadata and forwarding/rejection checks are new at
setup/copy/refactor. No solve/update scan, basis solve, coefficient conversion,
control copy, extra factorization or retained native owner is added there. One
Float64 function-valued keyword is a constructor-only test seam; future dispatch
and cost qualification remains required. Shared immutable Float64 lower metadata
and private work/history rules are unchanged. Whole direct refactor still builds
and publishes a complete replacement; its existing cost differs from ordinary
spare-buffer reuse and must be included in later complete-window comparisons.
Native scale-orientation/extraction and Markowitz dense-core work remain as in the
accepted plan. Diagnostic tests use owned snapshots, exact Rational-token oracles,
private20control copies and fixed5scalar observations; these are correctness costs,
not production work and not timed benchmark overhead. No new unbounded log/cache.
No numerical safeguard, tolerance, precision, coefficient or strategy is changed.

## Overlay preparation and next step

prepare-overlay.py reads71 tracked source/Project files directly from exact master
Git blobs, not diagnostic src. New red and candidate overlays each add two includes
after HH and two implementation files; all other original files inverse exactly.
They are stored in this plan's ignored workspace. It refuses existing destinations
and invalid mode, performs input validation before creating output, and never copies
Manifest/LocalPreferences or invokes Julia/Pkg. Their environment is deliberately
not yet admitted. This Python builder was executed offline; Julia sources remain
UNEXECUTED. Old programs/raw/pins/reviews stay frozen; old failedcost1 and blockedcost2
are not reopened. NextTask2 is concrete driver, exact expected assertions/call ledger,
resource/output/manifest admission and independent review, BEFORE future RED/GREEN.
No launcher or executable admission is supplied here. CIoff/HHreuse disabled,
automationpaused. Future300s initial/onlypuretimeout600s bounds remain as planned.
