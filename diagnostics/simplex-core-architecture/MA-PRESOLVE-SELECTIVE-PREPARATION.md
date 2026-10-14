# MA-L: selective rational presolver MA preparation

Date: 2026-10-14. OFFLINE candidate/test preparation; all Julia remains UNEXECUTED.

## Scope and candidate

Implements Task1 of the accepted MA-K plan. Exact Rational{BigInt} model and
Vector{Tuple{Int,Rational{BigInt}}} row dispatch considers only length8. Other
lengths invoke the unchanged generic method; other model/container types retain
that method directly. The actual production helper, tests, dependencies, CI and
master are unchanged. Aggregation's2–8/fill10/update200000 caps are untouched.

The candidate starts with the original arithmetic. It counts at most two actual
nonzero unequal-denominator endpoint additions by original row position3, with
both pivot/activity endpoints and both unequal current bounds finite. At the
second eligible addition a one-shot same-sign and >=129-bit numerator predicate
selects fresh scratch; failure or arrival at position4 permanently declines.
After selection all nonzero additions use three private rationals plus three
BigInt buffers, including equal-denominator additions. Zero/shared activity
shortcuts, products/conversions and final predicates are retained. No prefix
recompute, pre-scan or cache. The generic body and entire final comparison block
are byte-exact. Whole specialized-body inverse has six explicit transformations;
a separate diagnostic copy has eight reversible tracing transformations.

## Canonical future inputs and tests

Use results/MA-L/{reference.jl,candidate.jl,candidate-trace.jl,
test-helpers-reviewed.jl,tests-reviewed.jl,fixtures.jl,
extra-fixtures-reviewed.jl}. Combine MAL_FIXTURES and MAL_EXTRA_FIXTURES once
outside timing. All files define data/functions only; no driver or launcher is
prepared here. MA-M must bind actual imports/aliases/paths/commands and exact
loading arrangement before executing any Julia. Do not use superseded
extra-fixtures.jl, tests.jl or test-helpers.jl as canonical future inputs.

222 correctness fixtures include the frozen76 cost cases (24 targets/52 controls)
and146 additional cases. There are39 finite tight triples (inside/equality/
outside, expected true/true/false), all8 pivot positions and both signs, exact
128/129/130-bit numerator boundaries, trigger positions2/3/4, ordinal1 rejection,
opposite signs, infinite bounds before/after selection, fixed prefix followed
by divergence, shared numerator/denominator/input objects, zero result then reuse,
an explicit equal-denominator addition after selection and zero coefficient.
Length9/custom no-length iterator and tuple cases are direct-helper fallbacks,
not public aggregation coverage. Six stored256 BigFloat low-bit cases run
prospectively at ambient64/512; two lossy conversion negative controls reject
incorrect expected values. Stored scalar/precision encodings are explicitly
checked before calls. Cost grid/threshold/schedule from MA-K remain unchanged.

Prospective Test assertions:222×17 ordinary per-fixture predicates +9 alias
predicates +2 lossy negative controls +1 active equal-denominator predicate
+1 changed-snapshot negative control =3787 GREEN assertions. Original route RED
has8 passing numerical/preservation assertions and exactly2 expected scratch
assertion failures, in two selected cases. These are NOT executed test results.
GREEN calls four helpers per fixture (production/reference/candidate/traced),
888 entries; RED adds4 reference entries. Diagnostic private-add trace guards
cover1345 prospective additions, not additional Test assertions. Test builders,
corner enumeration, snapshots/strings/leaf comparisons are outside any future
cost window and are not proposed production work. They allocate and consume
qualification time; the MA-M first-process cap must include them.

## Offline checks and preserved correction

Initial source-check.json has28/29 PASS and one FALSE route expectation gate,
exit1 preserved. A supplemental zero-coefficient case inherited route_count=1
from the unit case, but zero at its third coefficient removes that sole eligible
addition. route-diagnosis.json identifies only this mismatch. route-fix.json
changes that metadata count to0 in separate extra-fixtures-reviewed files,
without changing any scalar, bound, expected Bool, candidate or cost case.
The separate source-check-final.py was executed once:29/29 PASS,37 read-time
hashes, all222 independent corner-oracle/route expectations, literal data
bindings and full candidate/trace inverses checked. No Julia parsing/dispatch,
mutation, allocation or timing acceptance follows from these Python checks.

A separate input-bindings supplement has5/5 PASS. It adds one assertion per
fixture binding every constructed stored scalar and BigFloat precision to the
canonical encoding; original tests and their source-check hashes remain intact.
The initial3565 assertion inventory maps to those original tests. The canonical
reviewed tests have3787 prospective assertions, with unchanged numerical inputs.
All generators/checks are one-shot and frozen; never rerun old accepted scripts.

## Computational work and memory

Frequency: one call per eligible equality/candidate pivot. Short typed rows add
one length check and invoke dispatch. Q8 adds position/counter/decision state;
check_pair short-circuits after a decision or position4. While pending, it adds
endpoint/finite checks and a bound equality observation reused by the original
min-product branch. For a zero minimum bound that equality can be additional;
it is not claimed free. At most two public base2 numerator digit queries and
sign checks occur once. BigInt arithmetic/comparison scales with limb lengths.

Selected calls allocate nine private mutable BigInt leaves with variable limb
capacity, with up to four pool/endpoint identity comparisons per private add.
Equal-denominator private work copies the denominator and normalizes by gcd;
this is required to prevent sharing a later-mutated scratch denominator. No new
vector/matrix traversal, basis solve, factorization, persistent cache or retained
model owner is introduced. Pool references stay local and cease mutation before
final predicates; GC/native-free behavior is not established.

No production work or memory has been added. Potential selector and false-positive
scratch costs remain UNQUALIFIED, so no performance/promotion claim is made.
MA-M must reject the fixed candidate if any of the76 cases misses its declared
allocation/time gate. Existing MA-J unconditional and MA-I rejection remain.

## Next boundary

Obtain fresh independent MA-L source/test/work review, then a separate exact
MA-M launcher/pin/auditor admission. Standing short-run human permission persists;
no new permission question is needed, but review acceptance here is offline only.
Maximum later schedule is three serial inclusive120-second processes, no retry,
with the existing memory/process guards. Whole-presolver integration remains a
separate conditional plan after component acceptance. Automation paused, CI off,
HH disabled; broader plan remains open.
