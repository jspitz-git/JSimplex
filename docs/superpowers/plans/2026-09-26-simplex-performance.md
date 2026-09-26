# Simplex performance follow-up

Base: `b69e266`. Worktree: `.worktrees/simplex-performance`.
Branch: `fix/simplex-performance`.

The user requests practical improvements to the existing solvers, specifically
old stabilization overhead, working in input precision before expensive rescue,
and the cost of long basis-update histories. This is sequential diagnosis and
bounded repair of existing paths, not another all-features rollout.

## Constraints and evidence

- Keep committed code, comments, reports and commit messages in English.
- Commit each verified change. Do not merge or push this new branch implicitly.
- Preserve feasibility tolerances and original-model certification.
- Measure warm solves separately from compilation and profiling overhead.
- Use the supplied NetLib, MIPLib and mps corpora; MIP cases are LP relaxations.
- Runtime completion measurements allow at least 360 seconds. Medium remains
  eligible under the 24-GiB WSL budget. Never solve big, largo or AnyMod in full.
- Run numerical jobs sequentially. Preserve failures and unfinished runs.
- Use exact or high-precision arithmetic as a test oracle; ordinary solver
  operations should stay in the problem's working type.

## Sequence

1. Profile fast0507, runtime and medium; compare short and long update histories.
   Separate basis kernels, scans, ratio tests, refactors and rescue arithmetic.
2. Remove unnecessary arbitrary-precision residual evaluation. Try native
   compensated dot products with an error enclosure before the existing wide
   fallback. Check cancellation, underflow/overflow, transpose solves and false
   acceptance against exact input arithmetic. This does not weaken tolerances.
3. Address measured basis-update and legacy-loop bottlenecks with isolated
   changes, preserving pivot behavior where possible. Measure complete solves
   and operation costs; changing the update interval alone is not a repair.
4. Validate the resulting changes with targeted regression tests, the complete
   suite and external problems. Report remaining gaps rather than promise parity
   with HiGHS/Clp from their user-reported timings.

## Initial findings

The first fast0507 legacy-dual profile has substantial cost in repeated full
workspace validation, CSC pricing and sorting bound-flipping candidates. PFI
solves are a minority. Raising the initial update interval from 20 to 500
changes the path (6,624 versus 6,884 steps), so these are not matched kernel
comparisons. Native residual quality currently switches to BigFloat when a
length-based rounding bound exceeds one quarter of the numerical tolerance,
even for a zero residual. Test this performance regression directly.

For native compensated residuals, use the error-free sum/product approach and
error enclosure of Ogita, Rump and Oishi, *Accurate Sum and Dot Product*,
[Algorithm 5.8](https://www.tuhh.de/ti3/paper/rump/OgRuOi05.pdf).
The error enclosure must account for the denominator's rounding as well as the
residual. Exceptional range or an inconclusive native check retains the wide
fallback. No working basis or pivot decision is promoted by this check.

Local raw evidence and progress live in `.superpowers/performance/` and are
retained for interruption recovery.
