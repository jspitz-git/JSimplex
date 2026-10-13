# Markowitz row-count fusion: production integration

The exact qualified change is integrated as master `6f68e24e8ddac42b948da8fcc2d636c010751194` from production
commit `99da53ebfa0e40a37880a5d764a92ebce43a7e44`. Expected RED is20pass/fourworkfailures;
actual GREEN is722/722 and actual master324/324, with separate passing audits.
Independent GREEN review accepted the actual change and integration; master result
and final publication reviews are recorded separately under S4-AD-green-bounded.
Two failed diagnostic attempts are preserved and are not counted as passing.

## Exact production change

The sparse Markowitz constructor now accumulates its initial nonzero count while
reading active row lengths for singleton discovery. The prior separate traversal
of all H retained rows is removed. Full row AND column dictionary resets remain;
tails are cleared before input filling, so their lengths are zero. Dense bypass,
scalar arithmetic, pivot ordering, safeguards and retained owners are unchanged.
The production file is byte-identical to the S4-AB/S4-AC whole-source candidate.
This removes H redundant length queries per sparse construction/refactor and
adds no buffer, solve, full-vector scan, conversion, cache or retained memory.
Arbitrary side-effectful/throwing custom length ordering remains outside the
qualified Dict/OrderedDict contract.

The permanent test appends exactly46 lines to the unchanged4188-byte workspace
test prefix. Its isolated dictionary wrapper observes actual constructor length
queries for n3/8,H=n/64. Six assertions per case check SingularException(1), row
reads, row AND column owners/capacities and cleared backing dictionaries.
There are four new tiny singular attempts and no new permanent public solves.
Cold test instrumentation creates139 row and139 column wrappers/dictionaries,
plus fixed owner/count/expected vectors; these source counts are not allocation
measurements. Existing lifecycle tests remain intact.

## Failed attempts and correction

The initial RED consumed one reservation but stopped before test inclusion:
Test.push_testset was undefined in installed Julia1.13.0. Its original admission
incorrectly accepted this API. Original driver/review/pins, exit1, missing structured
results and false audit remain frozen. A separate amendment uses installed
Test.@with_testset and verifies parent/depth restoration. The corrected RED
has exactly20 passes/four expected failures/no errors and preserves exit1.
The Test failure displays abbreviate long vectors; RED proves the precise failing
expression, not a complete serialized vector census. S4-AB's separate qualified
raw vectors supply the full read-vector comparison.

The first GREEN consumed its120s reservation and was terminated at120.068734s,
child-15/guard1, while the stack was in LLVM compilation in the existing public
solve testset. There was no tests.toml; no earlier pass counts or ambient-state
pass are inferred. This identifies the interruption site, not total compilation
time or a production defect. All689 pins remained unchanged;121 samples had
minimum availableRAM20870740KiB and swap0. Independent review rejected qualification
and accepted only this diagnostic account.

A separately admitted replacement GREEN has a300s cap under standing human
short-attempt permission; master retains120s. No original allowance was reused.
Exact tests/order/options/precision/compiler settings are unchanged. New per-file
progress output is outside tests; final structured results remain mandatory.
Progress recomputes total counts: source-derived21 extra four-Int vectors/84entries
for GREEN and6/24 for master, cold diagnostic work only. No benchmark was repeated.

An earlier offline expected-count mistake (408 instead of308 in markowitz_tests)
was caught before Julia; original schedule/scripts and partial failed preparation
are preserved. Corrected GREEN total is324+308+90=722. The later copied120s schedule
field was corrected before new manifest creation to explicit300/120 stage caps;
original32 synthetic bindings map to separate before copies, with four additional
binding checks. No false record was rewritten as passing.

## Correctness and execution scope

| Attempt | Child result | Assertions | Inclusive seconds | Decision |
| --- | --- | --- | ---: | --- |
| Original RED | exit1, missing API | none executed | 2.005350 | Infrastructure failure, preserved |
| Corrected RED | exit1 |20pass,4expectedfail,0error |3.006584 | Expected regression accepted |
| Initial GREEN | signal15/wall_time | No structured result |120.068734 | Rejected, preserved |
| Bounded GREEN | exit0 |722pass,0fail/error/broken |278.161389 | All8audit gates PASS |
| Actual master | exit0 |324pass,0fail/error/broken |13.012678 | All8audit gates PASS |

Launch manifests contain637/672/689/727/749 pins respectively. Valid RED,
GREEN and master raw outputs each have six byte-identical portable files;
the two failed attempts have five, with missing tests.toml explicitly preserved.
GREEN278samples minRAM20722344KiB, master13samples minRAM21938580KiB; swap0.
Both final result sets preserve ambientBigFloat256/RoundNearest.
All44process groups AND sessions are absent; no Julia remains. No rerun of
accepted AB or AC artifacts occurred. The inclusive times are not benchmarks.

GREEN runs three complete files, including original allocation/regrowth, stored
BigFloat precision, pivot ties, sparse/dense construction and all four scalar
kinds. The existing public loop has16 solves and16 standalone workspace
initializations (four managers by Float32/64/BigFloat/RationalBigInt). Explicit
source entries outside public internals are56 constructor attempts164 refactors,
57factor copies377direct solves40replacements; these are not observed complete
backend/import budgets. Actual-master workspace validation has26 constructor
attempts148refactors40copies204direct solves and no public solve. No full-suite,
historical CI cause, observer-neutrality or complete native-work claim.

## Cost and review

Reuse the unchanged S4-AB qualification:648predicates,24paired lifecycles,
12cost cases240windows168measured compile/recompile-zero. Retained-capacity
Float32/64 paired median ratios0.932735/0.950450 support a narrow local benefit.
Other timings are mixed; dense bypass differences are not attributable to this
change. Side-median allocation events agree; there is no memory-saving, universal
or end-to-end speedup claim. Integration elapsed times include compilation/setup
and are not benchmarks. Independent actual-source review found no unnecessary
added production computational work, allocation or retained memory.

## Publication and continuation

Only src/markowitz_factorization.jl and the workspace test are in the production
commit and master cherry-pick. Primary .vscode/settings.json and both environments'
Manifest/LocalPreferences bytes were verified unchanged. No CI/dependency change.
The publication protocol requires a separate PASS closure, fixed complete names,
exact staged/committed blobs and atomic dual-ref push with remote verification;
see closure.json/publication.json in results/S4-AD-green-bounded. Numerical tests
are complete; those records establish final publication, not this narrative alone.

The first GREEN result review accidentally bound supplemental finalize.py while
its final completeness was still pending. A scope-only correction removed that
binding before integration; exact prior review bytes were reconstructed and
verified against the originally reported JSON SHA, then preserved with explicit
correction metadata. Source/test/numerical/integrate bindings were unchanged.

AC current STATUS/roadmap review/closure/publication bindings map ONLY to original
S4-AD before copies. Historical initial/replacement RED actual source/test hashes
map ONLY to S4-AD source/test before copies when the exact old SHA matches.
All older mappings and failed artifacts remain. No old accepted driver/auditor
was executed. Both diagnostic amendments have independent admissions and distinct
reservations/outputs. All evidence is frozen after publication. Automation stays
paused, CI disabled, HH reuse disabled. Broader S2/S3/S4/S5/S6 remain open;
MutableArithmetics implementation remains a pending separately scoped workstream.
