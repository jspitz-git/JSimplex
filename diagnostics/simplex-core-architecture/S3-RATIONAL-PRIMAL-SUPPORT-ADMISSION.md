# S3-G: rational primal support admission decision

## Decision

**The proposed support-only `Rational{BigInt}` primal-update route is NOT
ADMITTED under the existing ownership contract. Stop this consumer route.**
This is a source/design rejection, not a failed numerical experiment, a solver
bug, or a proof that every future sparse-value design is impossible. No
candidate, next equivalent inventory, driver, or numerical plan is created.

S3-F established the floating signed-zero and dual-cost-repair constraints.
G resolves the remaining exact-scalar question: installed Rational{BigInt}
arithmetic creates fresh mutable BigInt destinations even for subtraction of
zero. Omitting the write preserves the old scalar owners. Existing support
metadata certifies indices, not that changing this ownership is unobservable.
The authorized design must preserve ownership without new metadata or a full
admission scan; no eligible subset with omitted rows is established here.

## Installed scalar source and ownership

Read-time source is under the recorded local runtime installation
`/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/base/`.
`gmp.jl` and `rational.jl` were read and newly hashed; they were not retrospectively
added to a historical launch manifest. No Julia dispatch, import, loader, GMP
call or arithmetic experiment was executed.

`rational.jl:9–17` defines an immutable Rational containing numerator and
denominator fields. Their type here is mutable BigInt (`gmp.jl:63–73`).
`gmp.jl:1093–1099` generates both `*` and `-` with the destination
`unsafe_rational(BigInt(), BigInt())`. There is no zero-operand shortcut in that
outer method. `sub!` and `mul!` use those destinations; `sync_rational!`
(`gmp.jl:979–986`) updates the destination BigInt fields and returns the same
destination rational. Finite arithmetic delegates to GMP. Multiplication of
rational infinity by zero throws DivideError (`gmp.jl:1059–1069`), so the exact
trait alone does not even justify zero-product elision for arbitrary operands.
The ordinary caller checks finite steps; the direct helper does not.

A prospective ownership oracle needs no new LP: retain `old_num` and `old_den`
from one finite basic primal entry before a direct helper call with a zero
coefficient and finite step. The dense reference writes a value-equal rational
with different numerator and denominator objects. A support-only omitted row
retains both old objects. Check `===` on the two fields as well as value equality.
This is a source-derived discriminator, UNEXECUTED. It does not claim arbitrary
GMP mutation through callbacks is a supported solver operation or that a normal
solver trajectory has been observed to fail.

Container ownership does not establish scalar ownership. In `simplex.jl:465–471`,
recompute assigns `basic_primal[row]` to `workspace.primal[index]`. In
`simplex_pivot.jl:80`, staged state uses `copyto!` on the primal vector. These
assignments/copies do not recursively clone the mutable BigInt fields. They
show actual sharing mechanisms, not proof that every such alias remains alive
at every pivot. A direct caller may also retain a scalar reference. Disabling
observers cannot prove the absence of those references.

## Ordered admission analysis and prospective oracles

The attempted read-only admission would examine these conditions in order.
Every condition is necessary only for the prospective route, not a proposed new
exception in the existing helper. Failure means execute the original dense loop.

1. Require exactly T === Rational{BigInt}, hypersparse enabled and a finite step.
   Other scalars and nonfinite direct-helper calls retain dense behavior.
2. Require an existing cache, matching matrix and all six scratch owners, the
   direction exactly `scratch.row_solution`, matching dimensions and valid
   buffer 2. Do not call `_pipeline_vector!`, rebuild, compact, sort or construct.
3. Exclude overlapping primal/direction storage and require the ordinary valid
   basis/order contract. Vector identity/storage checks do not certify scalar
   field uniqueness. The Basis constructor copies indices but does not check
   uniqueness; generic direct calls cannot assume it.
4. Require that every omitted write may retain its old numerator/denominator
   without changing the required ownership behavior. **This condition has no
   certificate in current workspace/support state. Admission therefore stops.**

The admitted eligibility result is consequently false for this proposed
optimization; preserve the unchanged dense basis-row order and final entering
addition for all inputs. No always-false runtime predicate is added. Full
support offers no omission benefit and also stays dense.

| Review class | Outcome and prospective reference oracle |
| --- | --- |
| Finite exact scalars / mutable fields / infinity | Reject omission on ownership; retain the field identities before a zero-row update and require reference detachment. An infinite step with an omitted zero must retain the reference DivideError and prefix-write behavior. These oracles are unexecuted. |
| Overlapping arrays, repeated basic indices, entering already basic | Dense fallback; compare sequential writes, subsequent direction reads when arrays overlap, and the final entering addition after all basis rows. Do not reorder by support insertion order. |
| Missing, invalid, detached or mismatched support | Dense fallback without cache construction, support rebuild, or new scan. Oracle: original result/exception and unchanged support metadata/counters. Cancelled zero entries in a valid index list do not certify omitted-row ownership. |
| Observer and recovery boundaries | Dense fallback. Existing events expose workspace state (`simplex_diagnostics.jl:87–96`); recovery/refinement may invalidate support. A saved scalar or invalidated direction must not be treated as freshly owned solely because the cache object exists. |
| Full support, other scalar types, noncanonical direct calls | Original dense loop and entering addition unchanged; compare arithmetic order, exceptions and selected ownership, not just equal values. No broad type dispatch or helper-contract strengthening. |

The table specifies discriminators for a future separately authorized redesign;
it is not a test suite or permission to run one. No historical test was rerun.

## Work and memory

The unchanged helper visits m basis rows and performs m multiplications,
m subtractions and one final addition. For successful finite source paths,
the generated Rational{BigInt} operator entries explicitly construct four
BigInts per basis row and two for the entering addition, plus temporary rational
and MPQ machinery and native GMP work. This is a source-derived constructor
count, not observed allocation events, bytes, retained memory, or a complete
native budget. Arithmetic cost depends on operand limb lengths, not just m.

The hypothetical checks in steps 1–2 cost a scalar/type/policy/finite check,
cache presence, matrix identity, six owner comparisons, direction identity,
bounded dimension checks and one validity lookup. Step 3 would add alias/order
requirements; verifying arbitrary basis uniqueness needs traversal or existing
trusted metadata. Step 4 cannot recover external scalar aliases by an array
ownership test. Repeating dense writes/copies to detach omitted scalar owners
would retain an O(m) traversal and scalar work, so it does not satisfy this
support-only admission. Even an O(m) local scan is not a general proof that
outside references do not exist.

A hypothetical sparse body would visit the stored index-list length, including
cancelled zeros, rather than only mathematical nonzeros; insertion order and
alias dependencies matter. No such body is implemented. No new production
scans, solves, copies, conversions, checks or retained owners were introduced.
**No unnecessary NEW production work or memory cost exists in this documentation
change.** No benchmark is warranted; no speedup is inferred from omitted
operations or source constructor counts. All validation, DSE, BFRT and factor
work stays unchanged and outside this local cost account.

## Evidence and continuation

`results/S3-G/collect.py` was saved before one execution. Fourteen source gates
passed with eighteen bindings, including the installed scalar sources. The
fresh host record contains boot, refs, all 28 recorded groups AND sessions and
no matching process or Julia. The initial exploratory reads had nonexistent
filename guesses; those read errors supplied no evidence and changed no files.
Production/test/CI diff against master is empty. F audits were not rerun.

F closure, publication and final-review current STATUS/roadmap bindings now map
only to `results/S3-G/{STATUS.md,roadmap.md}.before-S3-G`. The earlier F snapshots
continue to resolve S2-E current bindings. All older mappings, failed records
and frozen artifacts are preserved. The original G plan remains unchanged;
this report and independent review are its completed decision record.

This route has reached its specified stop condition. Do not create S3-H as an
equivalent ownership inventory or silently relax the ownership requirement.
S3 and the broader roadmap remain open; stopped directions stay stopped,
S2-E allowance stays consumed, S6-AQ needs new original evidence, HH reuse
stays disabled and CI stays off. A genuinely different concrete authorized
step or a human change to this boundary is needed before further work here.
