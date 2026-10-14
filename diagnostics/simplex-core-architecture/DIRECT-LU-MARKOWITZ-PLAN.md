# Common factor export and Markowitz direct LU: planning decision

Status: accepted plan for offline candidate/test preparation, 2026-10-14.
No Julia, imports, compilation, numerical tests or benchmarks were executed.
Production, tests, environment and master remain unchanged.

- [Specification](../../docs/superpowers/specs/2026-10-14-direct-lu-markowitz.md)
- [Implementation plan](../../docs/superpowers/plans/2026-10-14-direct-lu-markowitz.md)
- [Independent final review](results/DIRECT-LU-MARKOWITZ-PLAN/review-final.md)
- [Preserved initial review](results/DIRECT-LU-MARKOWITZ-PLAN/review-initial.md)

The plan covers an owned Float64 L/U/permutation/scaling export, explicit direct
FT/SS/BG factories with native and Markowitz backends, lifecycle correctness,
short paired component measurements and a separate tiny public integration check.
It reuses existing extraction, including Markowitz dense-core pivots. No public
option/default, dynamic sparse storage or arbitrary-precision direct export is
introduced by this planning decision. Native combined-solve refinement is absent
from direct substitution; preserved outer recovery is not equivalent stability.

Four initial P2 findings were resolved: sparse/core coupling coverage, conflicting
entering RHS instructions, omission of reusable backend refactors, and the native
refinement limitation. A further intermediate fixture defect was caught by static
pivot tracing and corrected before execution; the intermediate plan is preserved.
The final reviewer accepted the plan with no unresolved actionable findings and
no unnecessary work/memory requirement mandated by the design. This does not
validate an unwritten implementation or establish a speedup.

The cost schedule is 24cells x2processes x10pairs x2sides:960lifecycles,
960constructions,1920refactors,7680updates,15360FTRAN,7680BTRAN. Orientation solves
and correctness work are additional and must be bound in admission. All future
process ceilings together total420seconds:30 RED,90 correctness,2x90 cost,2x60
functional integration. Those are maxima, not predicted runtimes or permission to
extend a timeout. No large MPS/full-suite solve is part of this plan.

Next: offline Tasks1–2 implementation/test preparation and independent review;
only then exact short-run admission under standing human numerical permission.
All old raw results/scripts remain frozen. Current previous closure/publication
continuation SHA keys map to this step's before copies as recorded in
results/DIRECT-LU-MARKOWITZ-PLAN/continuation.json; old mappings remain unchanged.
The user redirected active work from micro-optimizations; the older wider plan
is not declared complete. CI remains off, HH reuse disabled, automation paused.
