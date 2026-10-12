# S6-F/G: controlled artificial-row recovery fixture

The budget/cancellation test requires an unreliable initial BTRAN row. Native
roundoff does not guarantee that precondition on every platform. S6-E established
a sufficient mechanism for the historical 96 failed predicates, not the actual
CI backend cause or an exact CI trajectory. This change makes the precondition
explicit through a test-only factor adapter; production removal remains unchanged.

## Change and ownership

Only the budget/cancel/exception testset uses the controlled fixture. Its original
six assertions per case remain unchanged. Both neighboring natural-fixture testsets
are byte-identical to master a465da5. A unique test factor delegates real BTRAN,
then replaces exactly the first six-element unit-row result with captured finite
binary64 BAD_ROW data. An independent basis/solve-quality probe verifies rejection.
Subsequent correction solves use the real owned factor. Forward, ordinary-forward,
prepared-destination invalidation, finite, refactor and update methods explicitly
forward; the original workspace retains its real factor type for final adoption.
The adapter asserts hypersparse is disabled. It introduces no production hooks,
method overwrites on production types, tolerance changes or precision changes.

## Evidence

- S6-F adapter-1: 36 triples across four native managers and nine modes. Ordinary
  factor and disabled adapter match recorded selected state with Julia isequal.
  Enabled cases prove exactly one injection, correction reachability, budget/
  checked/dual exclusions, cancellation, exact callback exception identity, strict
  pivot rejection, original infeasibility rejection, successful correction and
  exact reliable-row control. 396 qualification plus 168 original assertions pass;
  exit0, 14 audit gates, 599 independently checked pins.
- S6-G red-1: with helpers/preconditions installed but the natural constructor
  retained, 196 pass and exactly 56 expected reachability failures (28 type and
  28 hit checks). All 168 original semantic assertions and 28 quality preconditions
  pass; no errors. Frozen RED source/log are retained; all seven audit gates pass.
- S6-G green-1: constructor switched to controlled fixture; full file passes
  348/348 (48 + 252 + 48), exit0. All 12 audit gates pass, including independent
  whole-pin inventory, actual source/test hashes and unchanged neighboring tests.
  Runner374520/child374524/driver374512 separately absent, no Julia on boot
  20de7dde-704e-41c8-bee7-b8511c0a86b0 after completion.

Portable evidence is results/S6-F and results/S6-G; raw attempts and pin inventories
remain under .superpowers/simplex-core-architecture. Accepted attempts must not be
rerun against the changed permanent test: the S6-F source was the original oracle.

## Computational work and limitations

Production execution frequency, arithmetic, allocations and retained memory are
unchanged. Test setup adds one owned wrapper/workspace shell per controlled case;
all original owned fields are reused. Each adapted BTRAN adds a call counter and
branch; one six-element copy occurs per case, after a real solve. The independent
quality precondition adds one small basis assembly and O(n+nnz(B)) quality work per
case with owned scratch; no global workspace cache is retained. S6-F uses bounded
snapshots and fresh post-attempt quality fixtures; this is diagnostic work only.
No production benchmark or speed claim is warranted by this test-only change.

Coverage is local Julia1.13.0 AArch64, single Julia/BLAS thread, native managers,
Float64 controlled rows and default dense solve path. Neighboring natural tests
retain Float32/Float64/Rational coverage. Disabled equality covers recorded fields,
not all workspace bytes. Injection fixes the row precondition; later native
correction/pivot arithmetic remains real and platform-dependent. Actual x64 CI
success remains unverified; CI remains manually disabled. Other historical CI
families and the full S6 gate remain open. Fresh independent review accepted with no findings (see S6-ARTIFICIAL-FIXTURE-REVIEW.md).
Testa9be911 is integrated as master8516e0d. Master-1 passes348/348 with all13audit
gates, independent pins/source and original user-file hashes. No Julia remains;
runner375704/child375705/driver375695 separately absent on the recorded boot.
