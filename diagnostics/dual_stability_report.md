# Dual simplex stability follow-up

The solver now checks the residual of `Bᵀρ = e` before applying the dual ratio
test whenever the basis has incremental updates. A failed check refactorizes
the current basis and repeats the pivot decision. The existing `Bd = a`
direction check remains in place. A two-row regression demonstrates the gap:
its stale factor gives an inaccurate tableau row while the selected entering
direction is exact, so the old direction check alone did not refactorize.

The small MIPLib `pk1` LP relaxation provides a separate degeneracy case. With
default steepest-edge pricing it reached 10,000 iterations without finishing;
all 10,000 entering reduced costs in the audited path were zero, and no cost
shifts were made. No full basis-and-state repeats appeared in that path.
Independent full-LU recalculations of the dual steepest-edge weights at
iterations 100, 500, 1,000, and 2,000 agreed with the stored weights within
about `1.2e-9` relative error. This points to the pricing path rather than a
weight-update error. On the same problem, Dantzig pricing finished in 793
iterations and Devex in 3,033–4,816 iterations, depending on basis update.

The new fallback uses Dantzig pricing after 256 consecutive zero dual steps
under floating steepest-edge pricing, provided primal infeasibility remains.
It leaves explicit Devex or Dantzig settings alone and does not perturb model
costs or feasibility tolerances. A counterfactual switch after 256 iterations
finished `pk1` at iteration 354. The production rule finished at iteration
353 with product-form updates and at 1,593 with Suhl–Suhl updates, both with
objective zero and original-model certification.

An eight-fixture LP-relaxation sweep used one and six BLAS threads, product-form
and Suhl–Suhl updates, a 10,000-iteration limit, and a 20-second limit per run.
All 32 post-change runs returned `OPTIMAL`. The seven other fixtures triggered
no tableau-row refreshes. `pk1` triggered one refresh with product-form and
two with Suhl–Suhl updates under either thread count. These small fixtures
check for regressions and unnecessary refreshes; they cannot establish the
behavior of a large ill-conditioned model. A full post-change `runtime.mps`
solve and a `medium.mps` anti-degeneracy run have not been performed.

A matched local prefix run on the reduced `runtime.mps` used one BLAS thread,
Suhl–Suhl updates, a refactorization interval of 50, and a 2,000-iteration
limit. Each version was run twice after constructing the same presolved and
scaled model. In the second repetition, the previous version took 4.13 seconds
and 40 full factorizations; the new version took 4.19 seconds and 45 full
factorizations. Both returned `ITERATION_LIMIT` at 2,000 iterations. This
single short prefix indicates a small local cost but does not measure the
later ill-conditioned part of `runtime.mps` or its full solve.
