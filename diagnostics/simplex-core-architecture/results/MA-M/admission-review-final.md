# MA-M final independent numerical admission review

ACCEPTED for the single bounded MA-M component sequence described by the corrected
canonical files. No outstanding blocking finding. This accepts technical launch
admission only, not executed correctness, performance, production integration or
promotion. The original rejected admission and246-file pins remain unchanged.

Canonical inputs are driver-reviewed.jl, launcher-reviewed.py, audit_reviewed.py,
commands-reviewed.json, admission-reviewed.md, required-paths-reviewed.json,
pins-reviewed.json, dependency-roots.json and the unchanged guard.py. The explicit
correction section of admission-reviewed.md supersedes its historical launcher/
commands names. Only launcher-reviewed.py run and its exact three frozen driver
commands are admitted; a failed process stops the sequence with no retry/tuning.

## Resolution of both initial findings

MAM-ADM-1 is resolved. Independently hashed all3814 inventory files, checked every
resolved path and required/files/inventory membership, and enumerated all71trees.
Tree membership matches and no directory/dangling symlink exists. The68 installed
package/stdlib candidate roots cover all50 non-JSimplex names in the active and
overlay manifests; root Project UUIDs match. All their src/ext files and Projects
are pinned. JSimplex itself is separately bound by Project/Manifest and every
current src file, with exact runtime entry-path check. Previously omitted
OrderedCollections, PrecompileTools, MathOptInterface and their manifest source
dependencies are present. Base and two available artifact trees are also bound.
The guard checks exact tree inventory before/after and the launcher checks added
source membership. Actual loaded module entry paths are recorded and must resolve
to pinned entries. These bindings do not establish cache confinement, native
loader graph closure or neutral import costs, and make no such claim.

MAM-ADM-2 is resolved. The corrected aggregate first checks every saved stage
file binding against current bytes and existence, then repeats stage validation
before reading raw data for cost gates. Changed or missing raw can no longer
inherit prior qualification. Stage validation rechecks current process/source/
review/reservation links and the complete raw/Test schema. Existing audit and
output artifacts remain exclusive, nonoverwriting records. The29-check correction
record is bound and unchanged; its synthetic checks were not rerun or imported.

## Preserved admission and numerical safeguards

The only Julia driver change is one untimed loaded-module-path dictionary in the
raw header. All candidate, reference, trace, tests, fixtures, exact oracles and
input preservation code remain byte-identical to the first review and accepted
MA-L. Commands differ only in the new driver filename. Test capture APIs/counts,
three-process ownership/resource/deadline controls, no-retry reservations and
all statistical gates remain as reviewed in admission-review.md.

Counts remain222 correctness fixtures and3787 prospective GREEN Pass assertions,
888 GREEN helper entries,8Pass/2Fail expected RED across4 reference entries.
Each of76 cases has3warm+7measured alternating pairs of128 calls in each of3
processes:4560windows,583680timed calls,1368warm/3192measured windows, plus456
first calls. Every process is capped at114seconds running plus6seconds termination
reserve and120seconds inclusive; cumulative subprocess cap360seconds. One Julia,
Julia/BLAS1,2GiB heap hint,8GiB VM,6GiB available RAM minimum and1GiB swap maximum
remain guarded. Any timeout, incomplete qualification, changed inputs, unexpected
RED/GREEN result, missing evidence or measured compilation prevents acceptance.

Five required classes remain covered: short/simple rows without expected scratch;
shared leaves/prefix divergence/zero-result reuse; infinities, signs, pivots and
tight boundaries; generic containers/scalars and BigFloat stored/ambient precision;
early expensive prefix with cheap/cancelled tails or late general work. The fixed
24target/52control gates cannot be relaxed after output. A fresh result review
must independently recompute them and verify source/input evidence.

## Computational work and memory assessment

No production code changed. No additional candidate scans, basis solves, scalar
conversion passes, scratch reuse across calls or retained model cache were added.
The correction adds a once-per-process module-path dictionary outside measurement
and broader source hashing/membership work in launch/audit setup. Those checks are
required evidence work and count toward guarded setup where applicable. Audit
validation repeats bounded metadata work, not numerical kernels. No material
unnecessary computational or retained-memory cost was identified in the correction.
The accepted candidate still has potentially wasted selector and nine-leaf setup
cost on controls; this remains unqualified until the fixed measurements pass.
Temporary limb storage and GC are not native-free proof. Sparse/dense whole-pass
or end-to-end effects remain outside this component admission. No speedup claim
follows from acceptance here.

No Julia/query/parser/import/compilation or numerical code was executed during
this review. No old script or new launcher/guard/auditor was imported or run.
Independent Python only read/hash-checked files and counted manifest membership.
