# Markowitz row-count fusion: bounded qualification

S4-AB completed one admitted, guarded component qualification. All 648 literal
predicates passed: 24 work, 456 lifecycle and 168 cost/correctness predicates.
The admitted auditor passed six gates and the separate postcheck passed seven.
The candidate removes a redundant row-length traversal without changing scalar
arithmetic, retained capacity, dictionary reset, pivot selection or safeguards.
Production source/test/environment/CI/master are unchanged. Independent result
review is recorded separately in results/S4-AB/result-review.md.

## Change and ownership contract

The original sparse constructor sums `length` over H retained row dictionaries,
then reads the n active row lengths while seeding singleton rows. The candidate
starts an Int count at zero and adds the already-read active lengths in that
singleton loop. The existing full reset has cleared every retained row/column
before input filling; rows beyond n are empty. The dense bypass returns before
this code and is unchanged. No scratch, cache, fields or retention policy is added.
Both H-dictionary clear passes remain. This is not capacity trimming.

The prospective whole-source candidate differs only at that count/loop. Executed
candidate-methods.jl contains the exact constructor and refactor method with two
new private diagnostic names and one routed constructor call. No existing method
was overwritten and no full module was cloned. Source reconstruction/inverses are
bound by the 624-pin manifest and independent admission. The whole-source candidate
is still uninstalled. Arbitrary side-effectful/throwing custom dictionary `length`
ordering is outside this scoped contract; Dict and OrderedDict are qualified.

## Correctness and work evidence

Four singular zero-matrix work cases use n3/8 and H=n/64, dirty tail entries and a
counting dictionary. Reference reads are exactly 2 for each active row and 1 for
each inactive retained row; candidate reads are 1 and 0. Thus H reads disappear.
Both sides throw SingularException(1), clear all dictionary contents and retain
row owners. These counts are runtime evidence for these four cases; removal of
H queries in other sparse constructions is a source deduction. Unexpected
exceptions cannot satisfy the failure predicate, though their original text is
not separately recorded inside this work helper. This is not a solver defect.

24 paired lifecycles cover Float32/Float64/ambient BigFloat/Rational{BigInt}, Dict
and OrderedDict, sparse/dense/stored-zero CSC small inputs. Each side goes through
24→6→6→24 with a saved factor copy. All selected numerical factor signatures
(permutations, packed factors, diagonal, dense core and sparse-pivot count) agree
at each stage. Forward/transpose known-ones solves pass (exact Rational, absolute
64eps(T) for floating types), live workspaces/row owners remain private and stable,
saved factors still solve the original input, and input values are preserved.
This is selected component coverage, not whole solver state or certification.
BigFloat uses the unchanged ambient precision/rounding; their numerical values
were not serialized, so this is not a separately qualified multi-precision sweep.

Successful source schedule: 80 constructors/attempts, 1152 refactors, 48 copies,
528 direct forward/transpose solves; the work helper also creates/resets eight
workspaces. These are explicit driver source entries, not independently captured
complete PREforward/native/import counts. Fixed diagnostic signatures, graph walks,
input copies and solution vectors are outside timed windows; GC neutrality is
not proved. No new production work or retained memory is introduced by the change.

## Whole-refactor measurements

Twelve cases use four types and sparse32, sparse32 after capacity256, or dense32.
Three warm and seven measured alternating pairs per case; four refactors/window.
240 windows total, 168 measured, all measured compile/recompile zero. Every pair
has equal selected factor signatures; terminal solves and input preservation pass.
All original samples and GC outliers are retained. Setup and initialization are
outside timing; elapsed guard duration is not a benchmark. Cost cases use
OrderedDict; Dict is covered for correctness, not separately timed.

| Type | Case | Paired median C/R | Full range | R / C bytes per refactor (side medians) | R / C events per refactor (side medians) |
| --- | --- | ---: | --- | ---: | ---: |
| Float32 | sparse | 1.000000 | 0.984962–1.000000 | 12 / 12 | 0.25 / 0.25 |
| Float32 | retained | 0.932735 | 0.638037–0.937220 | 12 / 12 | 0.25 / 0.25 |
| Float32 | dense | 0.994845 | 0.979592–1.000000 | 0 / 0 | 0 / 0 |
| Float64 | sparse | 1.007634 | 1.000000–1.015385 | 12 / 12 | 0.25 / 0.25 |
| Float64 | retained | 0.950450 | 0.362098–0.959276 | 12 / 12 | 0.25 / 0.25 |
| Float64 | dense | 1.000000 | 0.994872–1.005128 | 0 / 0 | 0 / 0 |
| BigFloat | sparse | 1.014433 | 0.935849–1.092929 | 29580 / 29580 | 308.25 / 308.25 |
| BigFloat | retained | 1.001681 | 0.892857–1.013817 | 29580 / 29580 | 308.25 / 308.25 |
| BigFloat | dense | 1.037189 | 0.455759–1.664048 | 2.10115e+06 / 2.10115e+06 | 21887 / 21887 |
| Rational{BigInt} | sparse | 1.006550 | 0.874754–2.819221 | 97132 / 97140 | 3122.25 / 3122.25 |
| Rational{BigInt} | retained | 0.987407 | 0.850746–1.007636 | 97044 / 97032 | 3122.25 / 3122.25 |
| Rational{BigInt} | dense | 0.923133 | 0.155788–3.414066 | 7.01915e+06 / 7.01805e+06 | 182497 / 182497 |

C/R below one means lower candidate time in that paired sample. Side medians are
not paired medians. The retained-capacity Float32/Float64 cases have local median
reductions of about 6.7%/5.0%; their reference-side timing outliers remain included.
Ordinary sparse and BigFloat/Rational results are mixed. The unchanged dense
bypass also varies, so its differences are not attributable to the removed scan.
Dense BigFloat measured GC totals R0/C0.0029655s; dense Rational R0.067304112/
C0.030089106s. Dense Rational ratio range0.155788–3.414066 demonstrates substantial
noise. There is no universal or end-to-end speedup claim.

Events are equal by side medians in all cases, and observed final backend graph
sizes agree in all twelve pairs. Small Rational byte differences are recorded,
not claimed as allocations removed by this integer-only change. Counter values
include existing runtime/native counter semantics; fractions per refactor are
window totals divided by four. Graph estimates are not live native-memory/free
proof. The evidence supports eliminating known redundant work and a narrow local
hardware-float benefit, not a memory optimization or uniform timing improvement.

## Admission, process, preservation and decision

Manifest a0acb394a93db4f636c6a60486b74788035340f5eb060d39d7069760e538d697
binds 624 files. Fresh gpt-6-astra admission accepted 15 checks and independently
hashed all pins before execution. One exclusive reservation/attempt, exit0,
27.021221489994787s inclusive; 27 resource samples, minimum available RAM
21820304KiB, swap0, terminal available22344924KiB. Runner165751/start8101717,
child165754/start8101745, bootdade7243-9103-4398-bb45-fa28fbc0be72. Full34groups
AND sessions absent and no Julia after exit. Six raw files are preserved byte
identically under results/S4-AB/qualification-1. Postcheck is explicitly a
post-exit supplement, not a launch pin. No retry, tuning or excluded long run.

The unchanged numerical schedule, source inverse, exact work discriminator and
bounded correctness results qualify the candidate for a subsequent concrete
permanent-test/source integration subplan, subject to independent result review.
They do not authorize automatic production promotion. That subplan must retain a
work-count regression, existing lifecycle/safeguard coverage and independently
review actual production/test edits. Do not repeat this qualification or tune its
fixtures. Broader S4/S6 and the original roadmap remain open; MA is pending.

MA-B current STATUS/roadmap bindings map ONLY to the S4-AB before copies; all older
mappings remain. The launch plan and all admitted inputs/raw/audits stay frozen.
Separate closure and explicit exact staged/committed names/blobs precede fail-fast
publication. Automation remains paused, CI disabled, HH reuse disabled. Short
future attempts retain standing human permission but need concrete admission.
