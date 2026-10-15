# Exact selected source budgets and retention

These are prospective call-site counts, not executed assertions or full native
work totals. budget.json is the fixed machine-readable oracle.

## Test assertions

Options: 48 option combinations *6copies *17fields +2roundtrips *17fields
+12backend/manager rejection checks +4other checks =4946.
Backend ownership:2policies *15checks +4legacy-wrapper checks +1invalidsymbol=35.
Lifecycle:8manager/policy combinations *196=1568. Per combination:61 first/reset
checks +41populated-spare copy checks +2*47failure/saved-copy checks.
Precision/factory:160nonFloat checks +36roundtrip +48default/rejection +1=245.
Five original neighbors:25constructor+4backend stability+4resize+19owned sparse
snapshot/singular+12BigFloat copy/reset=64. Whole GREEN6858; RED4expected failures.

## PRE-forward call-entry totals

| Entry | Main candidate tests | Original neighbors |
| --- | ---: | ---: |
| _basis_factorization | 114 (108success,6rejected) | 0 |
| _factorize_basis | 7 (6success,1rejected) | 6 |
| PFI constructors | 0 | 9 |
| FT/SS/BG constructors | 0 | 1each |
| raw UMFPACKBackend wrappers | 2 | 1 |
| manager refactorize! | 120 (16singular throws) | 6 |
| direct _refactorize_backend | 0 | 6 |
| manager copies | 24 | 3 |
| manager update attempts | 24 | 3 |
| forward_solve | 226 | 7 |
| transpose_solve | 202 | 6 |
| hypersparse forward attempts | 0 | 8 (6argument/dimension rejections) |
| hypersparse transpose | 0 | 2 |
| sparse_solve_view attempts | 2singular | 9 (1singular) |
| raw lu(check=false) | 1 | 1 |
| public solve/problem/iteration | 0 | 0 |

324helper output equations include32empty systems;292nonempty residuals are
recomputed exactly offline. Other nonFloat/hypersparse neighbor oracles remain
their unchanged tests. Wrapper count includes attempted call before an exception,
not recursive/internal backend work. Manager factories, default HH extraction,
Markowitz internals, triangular replacement and sparse-snapshot construction add
internal work. No complete PRE-forward native/import ledger is claimed.
The constructor inference neighbors still use their original @inferred checks;
diagnostic wrappers are specialized forwarding functions. Runtime inference is
unverified and may fail; such failure stops, never weakens the original tests.

## Driver-only work and memory

GREEN has a fixed2048-slot event vector and400-slot equation vector. Only the
selected prefix is filled; no unbounded stream. Each entry creates a small dict
and selected state tokens, controls at most20entries per active/spare state,
small outputs and RHS (dimension<=3 for main output tokens; neighbors<=12).
324equations copy dimensions0/2/3 CSC/RHS/output to fixed bounded records. The
original tests also copy tiny histories/controls/matrices. These observations
are outside production and not a GREEN performance claim. String/dict allocator
bytes are unknown until runtime, not a native-graph cap. No factors/native owners
are held in event records: only integer objectid strings, bits and type text.
Objectid tokens are process-local observations, not global ownership proofs;
original tests assert simultaneous owner identity and preserved values.

Cost output payload=22windows*(32+96+32+96)*48*8=2162688bytes;
Info payload=88*4*48*8=135168bytes. Combined numeric payload2297856bytes,
plus88*48 vector headers,88Info matrix headers, outer vectors, immutable RHS/CSC
inputs and per-window serialization strings/dicts. Base.summarysize of the fixed
buffers is recorded before timing; it is not native retained memory. Saved C
comparison is offline Python only. Native fill/graph snapshots8entries outside
windows; all90Info and20control tokens/window and4Info scalars/solve are saved.
Only active and private-spare owners remain through a window; old timed returns
are cleared before the next. GC is unforced and all observed GC retained.

No production code change in this task. Candidate's constant Symbol/enum overhead
and possible policy-induced fill remain unmeasured. No new per-solve production
scan, allocation API, factor solve, conversion, cache or retained owner is added.
