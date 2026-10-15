# Independent exact-stage RED admission

Decision: ACCEPTED for exactly one RED attempt with a 30-second inclusive cap.
No actionable findings. This review grants only exact-stage admission; it does
not attest to an executed test, successful runtime loading, numerical correctness,
a stage result, GREEN/cost admission, or production integration. No Julia query,
parser, import, compilation or numerical execution was performed. No seal,
launcher, guard.run, supervisor.run, old script or stage auditor was executed.

## Exact identity and preservation

HEAD: `0798705ae92aa2f908b7468439b984deccde4c68`. Master: `6f68e24e8ddac42b948da8fcc2d636c010751194`.
Boot: `284d2228-1d9a-4c5f-913c-b9f1098b5838`.
Sealed manifest SHA-256: `1a272c55f55a7147cf2bf1f835a21171bbb7845679ceffee78f0d0479fcc85ab`.

All 951 sealed file hashes and resolved paths were independently rechecked,
including every one of the 679 runtime bindings. The 872 preparation bindings
and all 873 final offline-review bindings match; the latter has exact membership,
accepted offline scope, and the correct preparation-manifest digest. The stage
contains exactly the 73 reference manifest files, each matching its source and
recorded hash. No stage symlink or hard-linked file exists (file link counts are
all one). Stage files are copies of unchanged actual source/environment; no
candidate source or candidate tests are selected. There is no staged/unstaged
tracked diff. Existing untracked LocalPreferences.toml and Manifest.toml are
pinned; the newly created run directory is expected. No pinned file was edited.

The exact run/config.json equals the sealed config and the definitions-only
control_reviewed.config('red') result. The command uses /bin/bash and the pinned
basis-memory/reproduce/julia.sh wrapper, --compiled-modules=existing,
--threads=1, --gcthreads=1,0, --heap-size-hint=2G, the exact red project,
test-driver-reviewed.jl, exact output directory, red phase, and exact stage path.
Wrapper source selects the pinned Julia 1.13.0 executable with startup disabled;
its legacy wrapper is read for depot paths, not executed. Loading environment
matches environment.json. LocalPreferences disables the JSimplex workload,
auto-precompile is off, package mode is offline, and driver checks
PrecompileTools.verbose before JSimplex import. Existing-module mode is not proof
of cache confinement or zero import work; source fallback and dependency
initialization remain inside the inclusive budget. Runtime syntax/loading has
not been exercised by this source-only review.

## Selected contract and driver API

red-contract.jl selects one testset and exactly four assertions, in this order:
missing SolverOptions.native_pivot_policy, JSimplex._NativePivotPolicy,
UMFPACKBackend.pivot_policy, and JSimplex._native_lu. The reference declarations
lack these fields/symbols; exact-symbol source checks agree. Its selected body
contains zero constructor/factor/refactor/copy/solve/update calls and zero native
entries. This is a missing-interface RED, not a solver failure. Import is additional
work and this is not a native-initialization trace.

The pinned Test 1.13 source provides @with_testset through scoped CURRENT_TESTSET
and TESTSET_DEPTH. Its nested testset inherits Capture, restores root scope
before Capture.finish records the child, and the driver serializes raw state in
finally before returning expected exit 1. No removed push_testset/pop_testset API
is used. A load failure can precede raw output and must fail closed; no repair
attempt is admitted. The saved-data oracle requires exactly four named failures,
zero pass/error/broken, no nested children, complete execution with no fatal error,
single Julia/BLAS threads, empty observation counts/events/equations. It preserves
raw failure text and checks expected process reason exit1 and returncode 1.

Eight synthetic malformed approvals were refused: wrong scope, wrong phase,
accepted=false, a finding, wrong manifest digest, missing member, extra member,
and wrong file digest. Nine synthetic RED records were refused: incomplete,
fatal, nonempty work count, event, equation, wrong failure marker, extra failure,
unexpected error, and multiple threads. These checks used only definitions-only
Python controls and the standalone AST-extracted saved-data test_results function;
they are not runtime test results and did not import or execute the stage auditor.

## Resource, identity and attempt lifecycle

Fresh full_host checked all 208 historical identifiers as both PGID and SID,
plus all process comm and readable executable identities for Julia. No match was
found; boot and both refs match the seal. The full fresh record is below.
Inaccessible system executable symlinks remain an explicitly recorded visibility
limit. Available memory was 22429608 KiB and used swap 0 KiB; both pass the
6-GiB available / at-most-1-GiB swap gate. pidfd APIs are available. Launch must
repeat the checks freshly; this snapshot is not a waiver for later drift.

launch-reviewed.py checks exact admission scope/phase/membership/digests, stage,
environment, refs, boot and full groups/sessions before reserving. Exclusive writes
make prehost, pins, reservation, logs, output and invocation non-reusable; even an
incomplete attempt remains consumed. It dispatches exactly one child command and
has no retry or stage-advance path. A global nonblocking lock and live-Julia check
protect numerical ownership. RLIMIT_AS is 8 GiB; heap hint is 2 GiB; Julia/BLAS
threads are one. RAM/swap are checked before, during and after execution.

The absolute guard deadline is launch start plus 22 seconds. Supervisor TERM is
at plus 24, KILL at plus 28, and reaping is required by plus 30. Outer invocation
and supervisor elapsed predicates include launch/import/output/termination;
timeout is always rejection. Owned termination uses pidfd, two identity reads,
boot/start_ticks/command, and both group/session membership; wrapper-to-executable
transition is checked through stable identity fields before freshly binding its
command. Unexpected descendants and failed closure reject. Posthost extends the
208 identifiers with both guard and child PGID/SID, and audit links identities,
command, reservation, raw output, pins, resources and loaded paths. Raw child exit
1 is retained; guard success means only the declared expected exit was observed.

No reservation, launcher log, launch pins, invocation, output or audit existed
when this review was written. RED has no numeric input fixture or input alias;
its empty inputs list and source contract select no MPS/LP parser or dataset.
A RED result still requires independent result review. GREEN and cost remain
separate, unadmitted stages behind their respective accepted predecessor gates.

## Computational work and memory

No unnecessary new production work, allocation or retained memory was found.
All 73 reference files are unchanged; no tolerance, precision, coefficient,
numerical safeguard or factor ownership behavior changes. The four metadata
assertions add no full-vector/matrix scan, solve, conversion, control copy or
update-chain traversal, at setup or in any iteration/candidate/recovery path.
The shared diagnostic support allocates 2048 event reference slots and 400 equation
reference slots once at import; RED leaves them unused and serializes empty slices.
Capture retains four failure strings and a single child testset. These bounded
cold allocations are disclosed; they do not grow with LP dimensions, nonzeros,
iterations, update-chain length or factor lifetime. Offline full-file hashing and
process scans are admission/guard work, not component-kernel measurements.
Import/compilation/native initialization costs are additional and constrained by
the same inclusive cap. No benchmark is warranted for this unchanged-production
RED admission, and no runtime speedup or universal zero-overhead claim is made.

## Fresh read-only host evidence

```json
{
  "time": 1792095077.067907,
  "boot_id": "284d2228-1d9a-4c5f-913c-b9f1098b5838",
  "groups": [
    3955,
    3956,
    9849,
    9850,
    9882,
    9883,
    9906,
    9907,
    14094,
    14095,
    14117,
    14118,
    14143,
    14144,
    19295,
    19296,
    19347,
    19348,
    19394,
    19395,
    23249,
    23257,
    49081,
    49084,
    52772,
    52774,
    53479,
    53481,
    60706,
    60708,
    61004,
    61005,
    63808,
    63815,
    64420,
    64422,
    69401,
    69402,
    69456,
    69458,
    69479,
    69480,
    71824,
    71826,
    75902,
    75907,
    76742,
    76746,
    84681,
    84689,
    86967,
    86968,
    87044,
    87045,
    89395,
    89399,
    90313,
    90323,
    99593,
    99594,
    99645,
    99646,
    99672,
    99673,
    107333,
    107335,
    107892,
    107893,
    107905,
    107906,
    107921,
    107922,
    107965,
    107966,
    111848,
    111849,
    111903,
    111904,
    112032,
    112033,
    117608,
    117609,
    118109,
    118110,
    128482,
    128483,
    135392,
    135393,
    136331,
    136332,
    156956,
    156957,
    160834,
    160835,
    165751,
    165754,
    170669,
    170670,
    174370,
    174371,
    175023,
    175024,
    175550,
    175551,
    176600,
    176601,
    177364,
    177365,
    177868,
    177869,
    190814,
    190815,
    192340,
    192341,
    194458,
    194459,
    194475,
    194477,
    194516,
    194517,
    194543,
    194544,
    194560,
    194561,
    194574,
    194575,
    194595,
    194596,
    194612,
    194613,
    194651,
    194652,
    194677,
    194678,
    194691,
    194692,
    194710,
    194711,
    194729,
    194730,
    194746,
    194747,
    194787,
    194788,
    194806,
    194807,
    194829,
    194830,
    194846,
    194847,
    194866,
    194867,
    194885,
    194886,
    194899,
    194900,
    194938,
    194939,
    204836,
    204837,
    207758,
    207763,
    207776,
    207777,
    207824,
    207825,
    207838,
    207839,
    207856,
    207857,
    207884,
    207885,
    207906,
    207907,
    207933,
    207934,
    207970,
    207971,
    207988,
    207989,
    208007,
    208008,
    208033,
    208034,
    208048,
    208049,
    208068,
    208069,
    208110,
    208111,
    208128,
    208129,
    208146,
    208147,
    208166,
    208167,
    208187,
    208188,
    208208,
    208209,
    208230,
    208250,
    208272,
    208273,
    223350,
    223351,
    223631,
    223632
  ],
  "matches": [],
  "unreadable_exe_pids": [
    1,
    2,
    6,
    43,
    87,
    91,
    185,
    187,
    188,
    192,
    219,
    220,
    221,
    225,
    228,
    229,
    247,
    252,
    268,
    274,
    284,
    410,
    454,
    457,
    679,
    680,
    61416
  ],
  "scope": "All process stat/comm and readable exe; inaccessible system exe symlinks are a visibility limit",
  "head": "0798705ae92aa2f908b7468439b984deccde4c68",
  "master": "6f68e24e8ddac42b948da8fcc2d636c010751194"
}
```
