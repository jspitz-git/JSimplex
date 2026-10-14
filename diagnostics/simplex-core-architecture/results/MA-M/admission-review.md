# MA-M independent initial admission review

REJECTED. Two blocking findings prevent numerical admission of these exact files.
No Julia was started, queried, parsed, imported or compiled. No old script or new
launcher, guard, auditor or preparation checker was executed or imported. Review
used static source reads and fresh standalone Python hash/count calculations.

## Blocking findings

1. **MAM-ADM-1 (P1): incomplete imported source closure.** `src/JSimplex.jl:6-7`
   imports OrderedCollections and PrecompileTools; included `src/moi.jl:1` imports
   MathOptInterface. None of their installed package source roots is in the246
   pinned files. Active Manifest entries do not authenticate on-disk package
   source. Task2 requires full import/source dependencies. Bind the concrete
   selected source roots and transitive dependencies, including membership checks
   against added source files. This is ordinary source binding, not a request to
   reopen cache confinement, module isolation, or numerical import probes.
2. **MAM-ADM-2 (P1): aggregate accepts stale qualification evidence.** `audit.py:71-74`
   trusts saved `all_passed` flags, then reads current raw files without checking
   their recorded stage hashes or current qualification schema. Changing a
   measured compile field after stage audit leaves the performance ratios intact
   and can still yield aggregate `accepted=true`. Timing/class edits are likewise
   unbound. Compare the current evidence against stored stage hashes and freshly
   validate schema/process links; fail closed on drift and preserve prior records.

## Verified scope and counts

All246 current file hashes and resolved paths match pins.json; required-paths,
files and inventory memberships agree and trees is empty. All existing accepted
MA-L review bindings still match. The guard is byte-identical to MA-J. The seven
canonical include names/order and aliases match qualification-inputs.json and
keep diagnostic methods separate from production. Installed Test source confirms
Pass/Fail/Error/Broken orig_expr fields, inherited custom nested testset types and
the finish/record pattern used here. No executed Test success is claimed.

Independent counting confirms222 fixtures partitioned33 selection,23 ownership,
102 boundary,52 fallback,12 tail;3787 prospective GREEN assertions,888 GREEN
helper entries,8Pass/2Fail actual expected RED assertions across4 reference
entries. The RED failure expression is specifically scratch==1. Exceptions and
unexpected results cannot qualify.76 cost cases are24 targets and52 controls.
Per process:1520 windows,194560 timed calls and152 first calls. Across3:
4560 windows,583680 timed calls,456 first calls;1368 warm/3192 measured windows.
Three warm and seven measured pairs/case,128 calls/window, parity reversal,
whole-call result checksum and fresh per-call scratch are present. Fixtures,
oracles, snapshots, strings and serialization remain outside timed windows.

Snapshot code checks rational leaf identity/value, array owners/content,
bound flags and BigFloat stored precision/owner. Every correctness helper and
first call is followed by preservation checking; each timed batch has the same
check. Ambient precision/rounding and trace clearing are checked. Accepted MA-L
inverse evidence still binds the candidate/reference/trace sources exactly.

## Process and audit assessment

Reservations use exclusive creation and reject a previous attempt. The persistent
lock, noJulia checks, historical138 groups AND sessions, new runner/child identity
records, unreaped leader, pidfd identity checks and session-aware termination are
present. The wrapper selects the exact Julia executable and disables startup;
Julia/BLAS1,2GiB heap hint,8GiB VM,6GiB RAM minimum and1GiB swap maximum are set.
Guard114 plus cleanup reserve6 and postguard inclusive120/cumulative360 checks
stop continuation on failure. These are bounded cooperative OS process controls,
not a real-time scheduling guarantee. No automatic retry or tuning occurs.

The stage schema checks ordered cases/windows/parity, results, preservation,
nonnegative finite metrics, positive time and zero measured compilation. Target
and control median/time/bytes/events gates match Task2, retain warm/GC/outliers,
and report all76. The aggregate evidence-link omission above remains blocking.

## Five review classes and computational work/memory

Short/simple controls remain covered with no expected scratch; shared leaves,
prefix divergence and zero reuse retain the reviewed trace/input checks; infinite
bounds, signs, pivots and tight endpoints retain frozen exact oracles; non-Q,
custom-container and BigFloat ambient mismatch retain generic/precision checks;
four adversarial tails and late-general controls retain identical rejection gates.

No production change or unnecessary new row/matrix traversal, basis solve,
conversion pass or persistent candidate cache was found in this admission.
At each candidate-pivot call the existing accepted candidate adds bounded selector
work and may create nine mutable scratch leaves with limb-sized storage. Whether
that work is unnecessary on controls is still UNQUALIFIED and must be measured.
The driver adds diagnostic full-input snapshots outside20 windows and2 first
calls/case, plus bounded corner enumeration and retained timing dictionaries;
these count toward process time/memory, not kernel timings. Qualification trace
work occurs only in process1 and is cleared. No speedup, native-free, dense/sparse
whole-presolver benefit or universal nonregression is established. A separate
integration review remains necessary after any component acceptance.

Preserve this rejected review and exact pins before correction. A fresh review of
revised source manifests/auditor is required; this record authorizes no launch.
