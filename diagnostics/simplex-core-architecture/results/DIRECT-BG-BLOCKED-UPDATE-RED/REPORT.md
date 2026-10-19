# Blocked BG U — RED300 result

The single admitted RED attempt did **not qualify**. Julia failed while loading
the ordinary staged JSimplex module, before the first test unit. The expected six
N026 failures were not reached. Zero saved assertions is not a passing RED result.

## Admission and actual execution

The user authorized one independently reviewed RED run with a 300-second inclusive
limit. The preparation and exact-stage admission were accepted before release.
The seal contains 1,880 files; the admission binds those files and the seal itself
(1,881 keys), with 2,182 independent admission checks. Fresh host/ref/environment
checks passed; all 268 prior groups AND sessions were absent. The actual waiting
outer's configured environment was verified; the independent review shell's PATH
difference and initial wrong-cwd refusal are preserved as procedural context.

One release, one reservation, one guarded Julia child and no retry occurred.
Julia exited 1 after 4.510998418 seconds inclusive of launch; the outer completed
with code 2 after 17.369819137 seconds including checks/auditor. These are execution
durations, not performance benchmarks. This was not a timeout.

## Failure and source cause

The raw log reports `UndefVarError: _NativePivotPolicy not defined in JSimplex`
at the staged `src/direct-factor.jl` type definition (line 3; field at line 10),
included by staged `src/JSimplex.jl:79`, from `driver.jl:3`.

Task2 `fixtures.py:64-66` copied `R/src` from the diagnostic checkout into the
ordinary stage, then added the previously prepared direct adapter. The staged
`factorization.jl` is byte-identical to the diagnostic file and has no policy enum.
The verified production master 26e2291745999f485a74f643298ca997d65c7205 defines
`_NativePivotPolicy` at `factorization.jl:17`. The adapter requires that API.
This is a source-baseline composition error, not evidence against blocked U
arithmetic, a numerical failure, or merely an include-order fix.

Earlier author checks, independent offline review and exact-run admission proved
hashes/inverses against the chosen sources but missed their cross-file API
incompatibility. Their original acceptance records remain unchanged. Runtime
loading had explicitly remained unqualified; the new failure now resolves that
uncertainty adversely. No claim of a successful syntax or dispatch check is made.

## Preserved result and closure

There is no `raw.toml` or unit output. The original auditor ran once and recorded
`all_passed=false`, `pure_timeout=false`, and `Missing raw/units`. Exit 1 alone is
insufficient: the expected named failures must actually execute. The launcher
correctly refused acceptance. No GREEN or repeated auditor/numerics was run.

Four resource samples had minimum available RAM 22,412,188 KiB and zero swap.
Child max RSS was 540,740 KiB; terminal available RAM was 22,634,740 KiB. External
closure independently confirmed absence of the old, outer, guard and child
groups AND sessions, with no visible Julia and unchanged boot/refs. Inaccessible
executable links remain the recorded visibility limit.

## Work, memory and next boundary

No production/candidate/test/environment/CI file was changed. No new production
work or retained-memory cost was introduced. The failed load gives no evidence
about blocked updates, allocation savings, numerical residuals or performance.
Diagnostic Python source checks, fixed metadata and preserved logs are cold work.

The next concrete step is a **separate offline staging repair** using the verified
production baseline that supplies the policy API. Preserve all current stage,
driver, pins and failed output. Reconcile every changed baseline file, existing
adapter/source inverses, exact candidate/test bytes, numerical/pivot policy,
required bindings and resource budget; inspect the full dependency interface,
not just the first missing symbol. Do not add an enum shim or relax an oracle.
Any revised driver/stage requires fresh independent preparation and exact-run
admission before a separate RED attempt. GREEN remains blocked on accepted RED.
No repair or additional run is included in this result closure.

Broader plan remains open; master/CI/HH state unchanged. See `result-review.md`
and `result-review.json` for independent saved-result review. Diagnostic acceptance
of this failure record must not be confused with RED qualification acceptance.
