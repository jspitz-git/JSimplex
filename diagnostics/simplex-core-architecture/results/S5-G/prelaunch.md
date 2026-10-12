# S5-G concrete prelaunch contract

One attempt only: `python3 results/S5-G/launcher.py run` after an independently
accepted review, separate `freeze`, full independent rehash and fresh separate
host process/group check. Invocation paths are absolute in launcher.py. Driver
is frozen S5-F/driver-reviewed.jl, unchanged; original driver.jl is never executed.
Output .superpowers/simplex-core-architecture/S5-G/qualification-1/raw is a NEW
child directory of the guard output. The general guard owns an advisory lock,
reserves the child process group until cleanup, uses RLIMIT_AS 8 GiB, RAM 6 GiB /
swap 1 GiB admission and monitoring, and wall120 seconds from child start. Import,
source fallback and compilation count against this limit; monitoring granularity
can exceed 120 seconds by one polling interval plus termination cleanup.

Actual wrapper: /home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/
diagnostics/basis-memory/reproduce/julia.sh. It reads .superpowers/basis-chain-cost/
julia.sh with sed, constructs existing depot list, sets startup-file=no and execs
Julia1.13.0 aarch64. Nested shell is read, not executed. Both will be freshly pinned.
Installed command-line-interface.html explicitly documents existing as allowing old
cache files but disallowing new ones. Installed base/loading.jl:2727 attempts cached
loading; :2752 gates fresh parallel/serial compilecache on use_compiled_modules==1.
The launcher selects --compiled-modules=existing and does not issue a flag probe.
Pkg auto-precompile=false alone would not suffice. This establishes the ordinary
loader's no-new-compilecache route, not readonly cache confinement, initializer
work, actual selected cache validity, or arbitrary external process safety.
No package install/precompile, isolated modules, monkeypatch, or import benchmark.

Guard environment Julia/OPENBLAS/OMP/MKL 1; wrapper retains Julia/OPENBLAS1. Explicit
--threads=1 and --gcthreads=1,0; heap-size-hint=2G. No warmup, trial or extra solve.
Exactly stop/throw, existing fixture/native policy/128 requested bits unchanged.
Source-then-fresh ownership snapshots remain 88 arrays/215 encoded entries per
case. Retained graph during callback/postcapture and encoding work are not neutral
with respect to clock/memory. All imports/setup are separate from transfer deltas.

Frozen driver raw fields support independent Python audit.py. The auditor checks
source identity/value preservation, nonvacuous exact schema, Float64 bits vs rational
encodings, fresh scalar types/128-bit stored values, detached/equal source buffers,
fresh owned journal/model/basis storage and active aliases, history reset and levels/
cooldowns, unchanged checkpoint key and empty fresh caches/checkpoints, options/
policy semantics, callback/cause identities, ambient precision restoration and
shared work/budget. No _checkpoint_matches or lazy cache creation is allowed.
Kernel deltas: 1 FTRAN, 1..4 BTRAN (0..3 weight corrections), 1 refactorization,
all other existing keys0. Refactor_other1; possible correction_attempt/correction
only. These are finally counters, not complete PREforward or native/import work;
one ordinary weight BTRAN is untimed. No private clock/observer neutrality claim.
Source/fresh primal/prices/weights are observations, no new residual/certificate.

The new inventory includes all176 manifest paths, all S5-F artifacts, full src/test,
user/environment files, all runtime lib files, launcher dependencies, installed
loader/doc sources, new launcher/auditor/prelaunch review. No external MPS input;
forbidden big/largo/AnyMOD content identities still supplied to general freeze.
Runtime pinning is not complete dynamic loader-choice attribution. Auditor uses
exclusive output audit.json, preserves false gates and partial/no raw records.
Separate postrun host check verifies full runner/child groups and no Julia; separate
independent pin/user/source check and final review precede closure/publication.
No production/test/CI changes, no benchmark/speedup claim, no old scripts rerun.
