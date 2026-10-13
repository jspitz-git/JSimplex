# Markowitz row-count fusion: permanent test preparation

S4-AC completes the concrete offline integration preparation after accepted
S4-AB. The separate candidate source is byte-identical to S4-AB's qualified source.
The candidate test preserves the entire 4188-byte current file and appends one
46-line isolated module with six assertions across four fixtures (24 prospective
tests). Production/test/environment/CI/master are unchanged. No Julia query,
parser, import, compiler, numerical process or old script was executed here.

## Permanent regression

The test is named "Markowitz initial counts reuse active row length queries".
It catches reintroduction of the redundant construction sum by observing calls to
length on a test-owned AbstractDict backed by real Dict storage. No production
method is replaced. The real constructor and full workspace reset execute.
The four existing qualified fixtures are n3/8 with capacity n/64; a zero matrix
stops at SingularException(1) before elimination adds row-length calls. Dirty
last-row and last-column entries exercise reset even for retained tails.

Each case asserts expected exception/type index, active-row reads1/tail reads0,
row and column owner/capacity preservation, and empty row/column storage. Current
source should give four work failures and20passes, without unexpected errors;
that is a prospective expectation, NOT an observed failing Julia test. Unexpected
exceptions fail the type/index predicate. The wrapper does not mock a factor,
solve or numerical result. It records the real constructor's use of its storage.

Compared with the S4-AB work helper, this is one production side, no reference/
candidate pair, no TOML/CLI/raw maps and no diagnostic output collection. Test
assertions are permanent and normal Test storage is additional. Column owner
identity is newly explicit (S4-AB checked column emptiness but only row owners);
this source-supported expectation remains unexecuted until S4-AD admission.

## Computational work and memory

The production candidate adds no full scan, solve, copy, conversion, scratch,
cache or field. It removes H dictionary-length queries per sparse construction/
refactorization and reuses the n queries already needed for singleton seeding.
Both full H-dictionary clears, retained high-water capacity, arithmetic, pivot
order, thresholds, dense branches, failure handling and safeguards are unchanged.
This is neither capacity trimming nor a universal speedup claim.

The cold permanent test adds four tiny singular constructor attempts and four
workspace creations/pre-resets, no basis solves or successful factorization.
Capacities3+64+8+64 total139; source creates278 dictionary wrappers and278 backing
Dict objects across cases. Row/column owner copies, read arrays and expected-array
construction represent six explicit vector constructions per case,695 reference/
integer entries total (including temporary ones/zeros arrays). These are source
counts, not measured allocation counts or native-memory/GC proof. Test/catch and
sparse-input/framework storage add further cold cost. All checks happen after
failure; no production instrumentation or growing ledger is introduced.

The existing full test prefix remains byte-identical: manager reuse, pivot ties,
empty/shrink/regrow, failed-refactor live/saved solves, all four scalar types and
hardware-float zero-allocation regrowth. Its300 assertions are a source-derived
prospective count; with the append the full file expects324. No new benchmark is
needed for this exact candidate: reuse S4-AB's twelve-case/240-window comparison,
which showed local retained-capacity Float32/64 benefit and mixed other timings.
No blanket memory or end-to-end speedup claim follows.

## Concrete integration gate

The saved plan is docs/superpowers/plans/2026-10-13-markowitz-row-count-integration.md.
Next S4-AD prepares exact stage drivers, call schedules, source/runtime/command
pins, guards, reservations and independent admissions before execution. It must
bind actual Test output and run the new suffix against unchanged production first
(expected RED), then apply exactly the two candidate files for focused GREEN,
then integrate only the reviewed minimal source/test commit and validate actual
master. At most three new sequential120s-capped processes, each with a separate
admission/reservation. GREEN runs three named existing files; master runs the full
workspace file. Detailed include context, assertions and explicit public-call
schedules must be frozen at admission; this preparation is not launch admission.
Standing human short-run permission remains; no further permission question is
needed. Preserve failures; no silent numerical retry or old-driver reuse.

Twelve offline preparation checks bind28fresh file hashes. The source/test
candidate and test prefix relations are checked byte-for-byte. Textual checks
are preparation evidence, not runtime correctness, Julia parsing or TDD RED/GREEN.
Independent review is separate in results/S4-AC/review.md. No unnecessary new
production work or memory is proposed; new test overhead is bounded and cold.

S4-AB current result-review/closure/publication STATUS and roadmap hashes map ONLY
to S4-AC/STATUS.md.before-S4-AC and roadmap.md.before-S4-AC. All older mappings and
all accepted AB scripts/raw/reviews/pins remain frozen; never rerun/rewrite them.
Full34groups ANDsessions absent/noJulia with fresh boot/identity-aware preflights.
Separate PASS closure and exact complete staged/committed names/blobs precede
fail-fast push/remote verification. Automation paused, CI disabled, HH reuse
disabled; MA pending and the broader original plan remains open.
