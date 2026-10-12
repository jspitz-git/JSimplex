# S6-AH: narrow dual recovery acceptance contract

Decision: the identified AF subject evidence supports a NEW test-only recovery-budget
fixture proposal. It does not accept the whole AF qualification, replace its failed
INFEASIBLE oracle, or establish a successful infeasibility certificate. Independent
review of this decision and successor plan is required before implementation.
Base 6128620; master 3c0af5c. AH uses source and saved evidence only: zero Julia,
workspace, factor, solve, certificate, adapter implementation or permanent test edits.

## What the original tests require

Current dual_pivot_consistency_tests.jl remains byte-identical to the AF/AG source.
The two recovery groups have 108 original predicates across 20 public iterations:

| Group | Cases / predicates | Required behavior |
|---|---:|---|
| Failed recovery, four modes / four managers |16 / 80| Original terminal or wrapped observer exception; exactly one rejection; seven-field state equality including zero additional refactors; empty rejection lists and factor updates |
| Cancellation after refresh, four managers |4 / 28| TIME_LIMIT; five-field state equality; zero iterations; exactly one additional refactor; no completed pivot or bound flip; empty rejection lists |
| Untouched native duplicate safety |8 / 48| Preserve helper, legacy/adaptive public entry, nonsingular basis, unchanged basis/iterations and NUMERICAL_ERROR |
| Untouched direct small pivots |10 / 60| Preserve scalar/manager coverage, accepted direct pivot, zero refactors and zero rejections |

The first two groups test recovery, cancellation, exception propagation and publication.
They do not assert INFEASIBLE. The latter two and the original native helper remain
byte-identical. No native safety test is replaced by declared arithmetic.

## Evidence-based separation of contracts

AF made the additional control hypothesis that exact real solves imply INFEASIBLE.
All four controls violated it: NUMERICAL_ERROR with the saved certificate message.
AF remains NOT ACCEPTED: 265 pass / 4 failures, exit 1, false exit0/assertions269/
control_oracle gates, all_passed=false. Do not change that oracle, driver or auditor.
Its no_errors field is vacuous and excluded from this decision's evidence.

For a recovery fixture, the negative-control question is instead whether the real
unwrapped path produces correction_attempt or pivot_rejected, or publishes a pivot.
AF's four recorded controls have neither recovery event nor publication, and timed
work 1 FTRAN / 3 BTRAN / 1 ordinary refactor. Their NUMERICAL_ERROR alone cannot
separate them from the exhausted subjects; the actual event/work records do.
Controls DO contain pricing, pivot_proposed and refactor_other: no blanket no-events
claim is made. Controls use default policy, whereas nonrefresh subjects use their
original bounded policies; these are not matched-policy counterfactual pairs.

AG adds one new unwrapped, observer-free PFI observation, not four retroactive inputs.
Its source-bound final rho equals AE rho and satisfies B'rho=e2 exactly. Offline
source binary64 enclosure reconstruction straddles zero in the first column, whose
upper bound is infinite, so conservative certification refuses it. This explains
that new call's refusal without weakening safeguards. Other managers' private rows,
AF private certificate inputs and historical CI causes remain unobserved.

The new proposal uses AF's 20 separately identified subjects: 108 original predicates
plus 140 boundary checks all passed. AE real component outputs and AD represented
inequalities support the public path, and AF observes that path through the public
entry. This is evidence reuse for a narrower, explicitly declared contract, not a
renaming of AF's failed full qualification. A new implementation must still pass its
own changed-source and actual-master gates. No further control solve is needed just
to restate the saved outcome, and no INFEASIBLE oracle enters the permanent repair.

## Causal, ownership and work requirements carried forward

The dyadic B has top block [1 1;1-2^-23 1+2^-23] and identity lower block.
Column 5 duplicates column 1; RHS=-B[:,2], zero costs, nonnegative columns.
A wrapper is installed AFTER real setup. Each of the first TWO unit BTRAN outputs
must first genuinely equal rho=[-8388607/2,4194304,0,0], then declares rho-2^-22*e1.
AD's exact inequalities put its duplicate price below the negative eligibility
cutoff while the true prepared duplicate direction has zero pivot at row 2. Native
compensated correction receives [2^-22,2^-22,0,0], returns [2^-22,0,0,0], removes
that eligibility and reaches rejection. A single declaration is insufficient.
No quality result, ratio decision, event or certificate is fabricated.

| Path | Prepared / ordinary FTRAN | Unit / correction / cost BTRAN | Outer invalidations / metadata | Refactors / hits |
|---|---:|---:|---:|---:|
| Nonrefresh subjects |2 / 0|2 / 1 / 0|4 / 2|0 / 2|
| After-refresh cancellation |2 / 1|2 / 1 / 1|6 / 2|1 / 2|

Whole timed iteration work must independently be 2/3/0 and 3/4/1 (FTRAN/BTRAN/refactor).
Setup is separate. Native inner invalidations are additional to these outer entries.
Candidate and live workspaces SHARE the factor; candidate vector copies still exist.
Zero factor copies is not zero vector copies. Factor update and copy are unsupported
and must count then fail closed. Metadata must preserve the native unit RHS dispatch
and prepared-cache lifecycle; no substitution by dense ordinary solves is allowed.

AF captures correction before rejection once each, shared factor on staged events,
selected state preserved, rejection cleanup, and refresh event BEFORE both native
recomputations (event counts 2/3/1; final 3/4/1). Work survives candidate discard.
Original observer cancel/error/SingularException behavior must remain byte-identical;
permanent @test_throws must surround the direct public call, not a saved rethrow.
An outer read-only observer may add bounded identity/order/count checks without
changing those callbacks. This does not prove general observer neutrality.

All operation counters must advance BEFORE delegation and remain active after both
hits, including throwing forwards. AF's backend never threw; its observer exceptions
are not backend-throw accounting proof. The successor plan therefore explicitly bounds
driver-only sentinel microchecks, without real factorization or public iterations.
AF's static extra-unit negative budget check is reused only as oracle sensitivity,
not proof from a mutated production loop. No general lifecycle proof is claimed.

## Work, memory and limits

AH changes no production work, allocation or retained memory. Reading saved records
and hashing files introduces no solver cost; a benchmark would not answer this
contract question. The proposed permanent helper is cold test setup on dimension 4;
its wrapper must use owned fixed-size expected values and scalar counters, no growing
call/event ledgers or per-solve copies/conversions. Existing candidate copies and
production safeguards remain. No additional permanent iterations or timing claim.

Next: S6-AI, 2026-10-12-dual-budget-fixture-repair.md, only after fresh independent
numerical/work/memory review. S6-J remains rejected. CI disabled; broad S6, fullsuite,
x64, historical numerical cause and hidden arithmetic remain open. Existing AD copy
wording and AF vacuous no_errors Minors remain deferred in immutable evidence.
