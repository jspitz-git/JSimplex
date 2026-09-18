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

## Adaptive refactorization follow-up

The dual solver now lowers its effective basis-update interval after two
residual failures in updated solves before three clean scheduled
factorizations. It uses half the earliest observed bad update count, with a
minimum interval of one. Every three clean scheduled factorizations double
the interval, up to the configured limit. The original option remains
unchanged. Only failed `Bᵀρ=e` and `Bd=a` residual checks on updated factors
count as repair evidence; small pivots and fresh-LU failures do not.

A seven-row regression injects two inaccurate updated bases. One repair leaves
the 50-update limit in place; the second makes the next pivot refactorize.
After three clean cycles, the effective interval rises from one to two.
The 32 small fixture runs above still return `OPTIMAL` with the same iteration
and refactorization counts as before this follow-up.

In the same local 2,000-iteration `runtime.mps` prefix, adaptive
refactorization raised the full factorization count from 45 to 64 and the
second-run time from 4.19 to 4.63 seconds with one BLAS thread. Both runs
returned `ITERATION_LIMIT`. This measures the cost of extra early
factorizations; it does not establish whether they improve the later
numerically difficult part of the solve. A full run has not been performed.

## Upward adaptation follow-up

HiGHS documents a default `simplex_update_limit` of 5,000, which is a limit
rather than a guaranteed interval ([HiGHS options](https://github.com/ERGO-Code/HiGHS/blob/master/docs/src/options/definitions.md)).
In a local single-pass sweep of the first 2,000 reduced `runtime.mps` pivots,
product-form updates were fastest among the warmed runs with configured
intervals around 100–500; Suhl–Suhl was fastest around 50–100. The pivot
paths changed with interval, so these timings guide a conservative growth
ceiling rather than establish an optimum. On the small degenerate `pk1` LP,
fixed intervals from 20 to 2,000 changed the pivot count substantially.

The configured interval is now the initial floating-dual target. After three
clean scheduled factorization cycles with at least 75% nonzero dual steps in
each, the effective interval doubles. Growth stops during the zero-step
pricing fallback. Product-form updates can grow to at least 512; triangular
updates to at least 128. Their ceilings also scale to eight and four times
the configured initial interval respectively, capped at 4,096 unless the
user explicitly configured a higher initial interval. Two failed residual
checks still shorten the interval; one isolated repair pauses growth for
three clean cycles without shortening it.

The 24-row diagonal regression refactorizes less often on productive pivots
and retains the configured interval on zero dual steps. A separate regression
verifies that one repaired updated basis does not undo earlier growth. All 32
small fixture runs returned `OPTIMAL`. `pk1` retained its previous 353 and
1,593 pivot counts under product-form and Suhl–Suhl updates respectively;
`adlittle` changed from 104 to 103 and 107 to 122 pivots respectively.
Another regression grows an initial interval of 20 to 40, then injects
inaccurate solves after 30 and 25 updates. The interval shortens to 12,
computed from the observed failures rather than the initial setting.
The short `runtime.mps` prefix retained 64 full factorizations. Three second
one-thread repetitions took 4.50–4.78 seconds, compared with 4.63 seconds
before upward growth, so this prefix shows no clear speed change. A full
`runtime.mps` solve and a `medium.mps` run remain untested.

A matched one-thread comparison of the default product-form interval (20)
used the saved pre-growth commit `02c9825` and this version on the same
2,000-iteration reduced prefix. The warmed second runs made 108 and 84 full
factorizations and took 3.21 and 3.08 seconds respectively. Both reached
`ITERATION_LIMIT`; a changed pivot path can also affect these timings.
