# S0/S1 initial milestone review

Date: 2026-10-11. Independent reviewer: `s0_s1_review` (fresh context).
Range: documentation baseline `7d6a8e1` plus the local S0/S1 milestone.
Production reference: `fe839aa`.

## Findings and fixes

1. **P1, runner process-group cleanup.** A leader accepting SIGTERM could exit
   while a grandchild ignored it; the initial runner then released ownership.
   Both author and reviewer independently reproduced this with Python. The
   regression failed with `owned descendant survived the guard`. Fixed by
   observing leader exit using `waitid(WNOWAIT)`, retaining its PID/PGID until
   whole-group cleanup, and reaping afterward. A naturally exited leader with
   surviving descendants is an unsuccessful attempt. SIGTERM/interrupt cleanup
   preserves a final report and never signals unrelated groups.
2. **P2, directory symlink pinning.** `rglob` did not descend through directory
   symlinks and `is_file` omitted them. Two regressions failed: a preexisting
   directory link was accepted at freeze and an added one did not invalidate
   pins. Fixed by rejecting directory and dangling symlinks in pinned trees.
   Ordinary file links record both resolved path and bytes.

The fixes were verified by the author with regression tests and the full
Python guard suite; there was no second independent review of the fixes.
No findings were deferred or declined. The tests are maintained with the guard.

## Verification

Command from the active checkout:

```sh
python3 -B diagnostics/simplex-core-architecture/reproduce/test_guarded_run.py
```

Final result: **18 tests, all passed**. Coverage includes changed/deleted/added
pins, immutable pin manifests and attempt directories, lock contention, cold
memory/swap and live-Julia refusal, resource limits/thread environment, startup
failure, nonzero child exit, changed pins despite child exit 0, timeouts,
TERM-ignoring descendants, natural leader exit with descendants, runner SIGTERM,
unrelated process preservation, and forbidden content aliases. Host sensor
refusal tests replace only the sensor values; subprocess/lock/lifecycle tests use
real Python children. No Julia process is started by this suite.

Raw red/green logs are preserved in
`.superpowers/simplex-core-architecture/S0/`. Compact hashes and test results are
in [harness.json](results/S0/harness.json). Source hash audit matched all 70 files;
`git diff fe839aa -- src test Project.toml` was empty. Local Markdown links and
fixture TOML parsed successfully. The original worktree, main's settings change
and both local environment files are preserved.

## Numerical and work/memory assessment

Independent review confirmed the inventory's central claims against source:
four dual call-site boundaries are separated by possible mutation; local DSE
reuse already exists; logger callbacks separate repeated basis validation;
staged workspaces share problem/factor storage; row and direction residuals
certify different equations. The proposed owned-deadline contract remains a
hypothesis for S1-A, not an accepted production optimization.

**No unnecessary production work or retained memory was introduced.** There are
no production changes: no new per-iteration or per-candidate scans, solves,
conversions, copies or validity metadata. Diagnostic hashing is cold O(total
pinned bytes), streamed in 1 MiB chunks, with O(file count) retained metadata.
Resource logs are streamed at at most approximately one sample/second for long
attempts. Process enumeration and cleanup are runner-level work outside numerical
timings. During forced cleanup, ownership remains held until the owned group
has stopped; SIGKILL cannot forcibly complete uninterruptible kernel I/O.

S0 local harness/evidence and S1 inventory are reviewable deliverables. Long
phase-II instrumentation, calibration and reference remain pending, as do S1
production changes and numerical validation. No production speedup, solved
medium model or resolution of the separate test.mps failure is claimed.
