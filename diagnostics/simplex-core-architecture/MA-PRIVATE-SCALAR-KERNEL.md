# MA-A: private scalar MutableArithmetics measurement

## Decision

The user-requested isolated scalar dot experiment passed all 12 cases. Buffered
MutableArithmetics 1.8.1 reduced measured allocation traffic to zero and reduced
paired median time in every case. This supports investigating private scalar
scratch in a concrete future kernel. It does not admit a production replacement,
shared-scalar mutation, support omission, or a solver/end-to-end speedup.
Production, tests, project/environment configuration, CI and master are unchanged.

## Measured results

Times below are side medians in microseconds per complete dot; ratios are the
median and full range of seven paired buffered/plain window ratios. Each window
contains 32 dots. Bytes/events are per-dot medians of Julia aggregate GC counters,
which may include counted native allocations. They are not a native free ledger.

| Type / bits | Input | Plain µs | Buffered µs | Paired ratio [range] | Bytes plain → buffered | Events plain → buffered |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| BigFloat 128 | 32 dense | 7.138 | 0.869 | 0.1224 [0.1177, 0.1258] | 8320 → 0 | 260 → 0 |
| BigFloat 128 | 256 dense | 54.456 | 7.438 | 0.1364 [0.0140, 0.1482] | 65664 → 0 | 2052 → 0 |
| BigFloat 128 | 256 7/8 zeros (dense storage) | 49.997 | 3.947 | 0.0793 [0.0574, 0.0813] | 65664 → 0 | 2052 → 0 |
| BigFloat 256 | 32 dense | 7.197 | 1.266 | 0.1761 [0.1720, 0.1819] | 9360 → 0 | 260 → 0 |
| BigFloat 256 | 256 dense | 57.619 | 11.347 | 0.1992 [0.1465, 0.2013] | 73872 → 0 | 2052 → 0 |
| BigFloat 256 | 256 7/8 zeros (dense storage) | 49.622 | 4.281 | 0.0862 [0.0713, 0.0872] | 73872 → 0 | 2052 → 0 |
| BigFloat 512 | 32 dense | 8.072 | 1.825 | 0.2234 [0.1152, 0.2366] | 12480 → 0 | 325 → 0 |
| BigFloat 512 | 256 dense | 66.803 | 17.372 | 0.2587 [0.2427, 0.3113] | 98496 → 0 | 2565 → 0 |
| BigFloat 512 | 256 7/8 zeros (dense storage) | 52.222 | 5.056 | 0.0954 [0.0880, 0.1063] | 98496 → 0 | 2565 → 0 |
| Rational{BigInt} | 32 dense | 8.381 | 4.031 | 0.5023 [0.4032, 0.5538] | 21608 → 0 | 578 → 0 |
| Rational{BigInt} | 256 dense | 62.794 | 34.466 | 0.5442 [0.0847, 0.6136] | 172048 → 0 | 4600 → 0 |
| Rational{BigInt} | 256 7/8 zeros (dense storage) | 43.256 | 29.962 | 0.6879 [0.0608, 0.7766] | 164918 → 0 | 4155 → 0 |

All 84 measured buffered windows reported zero bytes/events and zero in-window
GC. All 168 measured windows reported zero compilation/recompilation. Several
plain windows incurred GC; every observation, including long GC windows, remains
in the paired ranges and medians. No outlier was discarded. This is one process,
small deterministic fixtures and short windows, not a confidence interval or
universal speedup. The zero-heavy case uses dense vectors and visits every entry;
it does not qualify sparse storage or support-skipping performance.

## Correctness, precision and ownership

The reference computes sequential `s = s + a[i]*b[i]`. The candidate resets a
private accumulator, then uses `MA.buffered_operate!(buffer, MA.add_mul, ...)`.
Installed specialized methods perform separate multiplication and addition; no
FMA, reassociation, tolerance change, dropped coefficient or raised precision.
BigFloat runs at 128, 256 and 512 bits under RoundNearest. Rational inputs are
exact, with non-dyadic denominators and roughly 80-bit numerator terms.

Every one of 240 warm/measured outputs matches the Julia sequential reference.
An independent Python Fraction oracle reconstructs all actual rounded inputs,
rounds every multiplication/addition with nearest-even at the selected precision,
and matches every output. It independently recomputes the exact dot and the
predeclared gamma(2n)*sum(abs(products)) forward bound; Rational error is zero.
Input values, scratch owner identities and precision pass after every window;
ambient precision/rounding restore. Two BigFloat backing owners or twelve BigInt
scratch leaves are pairwise private and disjoint from input owners.

The output Ref borrows the accumulator: retaining independent results would need
an explicit copy. This contract is confined to the experiment. It does not prove
that solver-owned or aliased values may be mutated, and does not reopen S3-G.
NaN/Inf, signed-zero corner cases, exceptions, arbitrary mixed precisions and
unbounded Rational numerator/denominator growth are outside this qualification.

## Work and memory

Exactly 12 cases, one unmeasured reference per case, three warm and seven measured
alternating pairs, 32 dots/window: 7,692 dots and 1,394,816 multiply-add visits.
Both sides traverse the same arrays. No new scans, solves, conversions or copies
are introduced into a production path. Diagnostic input/oracle/owner checks,
serialization and graph queries occur outside timed windows. Full import/native
work is not instrumented or bounded by these kernel entry counts.

Scratch construction is recorded separately. BigFloat128/256/512 setup records
224/256/352 bytes and 6/6/8 events; Rational setup 672 bytes and 24 events.
Observed setup times span 0.3–2.7 µs; these isolated observations are not a cold
startup/JIT benchmark. Warmup can grow limb capacity. Measured steady-state zero
allocation therefore does not mean that construction or arbitrary future values
allocate nothing. Post-run scratch graph estimates are 144/176/240 bytes for
BigFloat and 456 bytes for Rational, not native ownership/free/peak-memory proof.
No unnecessary production work or retained memory was introduced; no production
code changed. Diagnostic scans and retained input/oracle records are deliberate
validation costs, not claimed neutral to overall process GC scheduling.

## Execution and provenance

One accepted 120-second capped Julia process, Julia/BLAS1, heap2GiB, VM8GiB,
RAMfloor6GiB/swapmax1GiB. Separate diagnostic Project declares MA/TOML and uses a
copy of the user's existing Manifest. No package resolution, installation or
precompile command; existing-only compiled modules. Actual MA source/version
checked at runtime; 622 launch pins checked before and after execution. This is
not cache confinement or a complete loader-choice capture.

Fresh independent gpt-6-astra admission accepted; nine reviewer gates, 12,312
independent rounding comparisons and 16 rejection checks. Author preparation
has 17 Python checks. A pre-seal field-name mistake expected `all_passed` instead
of review `accepted`; missing fail-fast in that outer shell then called the
launcher, which refused the absent allowance before reservation/guard/Julia.
Original null-returncode invocation and empty log are saved as `.before-seal`;
separate independent seal supplement confirms no numerical attempt occurred.
Corrected seal and numerical launch were separate successful commands. No Julia
retry, numerical tuning or raw rewrite occurred.

Completed process exit0, all raw case/window gates, six admitted audit gates and
seven supplementary postchecks pass. Six original raw files and portable copies
are byte-identical. Three resource samples: minimum available RAM22,136,620KiB,
swap0, terminal available RAM22,366,504KiB. Inclusive duration3.00522799299506s is
not a kernel benchmark. Full32 prior/current process groups AND sessions absent,
no Julia. `postcheck.py` is explicitly a post-exit supplement, not a launch pin.

Evidence: [results/MA-A](results/MA-A), including exact plan, driver, source pins,
authorization, admission, raw measurement, independent exact oracle and audit.
Final independent result review is [MA-A/result-review.md](results/MA-A/result-review.md).
All numerical scripts/raw/pins/reviews are frozen after completion; never rerun
this consumed attempt. AA current continuation bindings map ONLY to MA-A's
STATUS.md.before-MA-A and roadmap.md.before-MA-A; all older mappings remain.
Automation stays paused. Broader S2/S3/S4/S5/S6 gates remain open.
