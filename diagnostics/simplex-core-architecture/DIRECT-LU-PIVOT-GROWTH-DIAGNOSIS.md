# Direct LU: saved pivot growth and cancellation diagnosis

## Decision

The saved sparse96 B4 factors demonstrate large element growth and cancellation
in the native UMFPACK reference. This supplies a concrete numerical mechanism for
the failed DSE qualification, despite a well-conditioned input. It is not evidence
of an FT update-history defect, nor by itself a UMFPACK implementation bug.
No new solver execution, control change, benchmark or production change occurred.
The original cost1 failure and the diagnostic's three residual failures remain
failures; cost2 remains blocked. No tolerance relaxation or candidate promotion.

Evidence: `results/DIRECT-LU-PIVOT-GROWTH-DIAGNOSIS/analysis.json` (20 checks),
new exact arithmetic on the two already saved factor snapshots and output vectors.
`analyze-2.py` is the executed canonical analysis. Initial `analyze.py` failed before
writing its output because a provenance filename included an extra `.h`; its
source and failure record are preserved. The separate version changes only that
filename. No old auditor, launcher or Julia driver was rerun.

## Input conditioning and factor growth are different

A column permutation places each unique largest row entry of B4 on its diagonal.
The largest absolute row sum is 153/32 and minimum strict dominance margin 103/32.
The usual infinity-norm inverse bound for strict row dominance therefore gives
`cond_inf(B4) <= 153/103 = 1.48544...`. Column permutations preserve this condition
number. This exact input bound does not control growth in a particular sparse LU.

| Saved quantity | Value |
| --- | ---: |
| max absolute original B4 entry | 4 |
| max absolute scaled B4 entry | 0.9411764705882353 |
| max absolute L entry | 8.06201920231798 |
| max absolute U entry (31,31) | 231235.78947368418 |
| max U / max scaled B4 | 245688.02631578944 |
| max U / max original B4 | 57808.947368421046 |

These are final-factor growth ratios, not a captured maximum over all intermediate
frontal matrices. Both fresh and prefix factors are identical except Info. The
native input CSC equals the frozen B4, and the captured scaling flag is 1
(multiply exported Rs). Exact calculations retain all binary64 input bits.

## Local cancellation is directly visible

In U column31, rows25 through31 contain respectively approximately
0.888889, 6.789474, 54.736842, 441.289474, 3557.684211, 28682.118421,
and 231235.789474. The associated L rows contain multipliers near -8 and -0.5;
the complete exact row ledger is in the analysis. This is a stored algebraic
pattern, not a capture of native elimination order or pivot candidate decisions.

Factor position (31,31) maps to original B4 position (87,1), which is exactly zero.
The three nonzero terms of the exact product L*U at that position are:

| k | Exact stored-factor product | Approximation |
| --- | --- | ---: |
| 29 | -7823430314857525 / 4398046511104 | -1778.842105263158 |
| 30 | -7884080678298893 / 34359738368 | -229456.94736842104 |
| 31 | 7945201227633717 / 34359738368 | 231235.78947368418 |

Their absolute sum is about 462471.58, but their exact signed sum is
`-53/4398046511104`, about -1.20508e-11, rather than the target zero.
This is the largest entry of `L*U - (s.*B4)[p,q]`. The discrepancy is already
encoded in stored factors; it cannot be attributed to roundoff in this new exact
analysis. High growth makes cancellation-sensitive representation plausible
without bad input conditioning. The three terms identify the location and scale
of the lost identity, not the specific native instruction which rounded it.

For the stored DSE output, exact `U*x[q]` at rows29,30,31 is approximately
974.55647, 7857.07456, 63344.06552. These are algebraically derived quantities,
NOT captured intermediate solve vectors. Their subsequent multiplication by L
also combines large terms to recover the small scaled RHS. No new triangular
solve or synthetic floating-point replay was executed.

Recalculation reproduces the entire previous exact decomposition. At original
row87 the representation contribution is -1.56805291494e-11 and the combined
application consistency contribution is +5.32125912258e-11. Their difference is
`9928545/144115188075855872`, +6.88931203752e-11, 18.861415966 times the unchanged
qualification bound. Growth/cancellation supplies the missing numerical
mechanism; the exact native rounding sequence and the split between forward and
back substitution remain unobserved. Neither contribution is discarded.

## Actual controls and source interpretation

Installed `SparseArrays/src/solvers/wrappers.jl` binds zero-based constants;
metadata below uses the corresponding one-based Julia slots:

| Field | Slot | Captured value |
| --- | ---: | ---: |
| Info STRATEGY_USED | 19 | 1 = UNSYMMETRIC |
| Control PIVOT_TOLERANCE | 4 | binary64 0.1 |
| Control IRSTEP | 8 | 0 |
| Control DROPTOL | 19 | 0 |
| Info UMIN | 72 | 0.10526315789473684 |
| Info UMAX | 73 | 231235.78947368418 |
| Info RCOND | 68 | 4.552200078297842e-7 |

The retained versioned upstream UMFPACK header documents threshold partial
pivoting: a pivot can be accepted at tolerance times the largest column entry.
Tolerance 0.1 permits weaker pivots than full partial pivoting; observed L
multipliers above 8 are consistent with that allowance. Documentation explicitly
allows accuracy/work tradeoffs and does not guarantee improvement from a larger
threshold. The actual strategy is unsymmetric, so a diagnosis based on symmetric
diagonal preference would be incorrect. No dropping is requested by DROPTOL=0;
this is not a proof about every internal zero treatment.

Info RCOND is documented as min(abs(diag(U)))/max(abs(diag(U))). Recomputing that
ratio gives the saved value after binary64 rounding. It is a rough diagonal-ratio
estimate, not a contradiction of the exact condition bound for B4. The header's
UMAX prose repeats “smallest” erroneously; its macro comment, installed constant
and actual recomputed maximum resolve the meaning here.

The installed Julia wrapper and production `factorization.jl` remain bound as
read-time source evidence. The upstream header and its provenance are semantic
references, not proof of the installed native build or a trace of runtime pivot
selection. These fresh bindings are not retroactive launch pins.

## Consequence and next decision

Do not change the task3 fixture, tolerance, native controls or precision to force
the existing comparison through. The ordinary reference demonstrably failed its
frozen accuracy gate, independent of the new export/prototype implementation.
This diagnosis completes the bounded saved-evidence step.

The next concrete direction is a separate source/design plan for an explicit
native Float64 accuracy policy at factor construction, with a possible stronger
pivot threshold assessed against iterative refinement. Such a plan must preserve
default behavior initially, specify ownership/copy/refactor propagation and the
additional factor fill, work, solve scratch and memory costs, and freeze a short
correctness/cost comparison before any execution. It is a new policy experiment,
not a rerun of cost1 or permission to resume cost2. No remedy has yet been selected,
implemented or qualified; full partial pivoting is not a promised fix. This is a
proposal for a subsequent plan, not numerical admission.

## Work and memory review scope

There is no production-code change and thus no new per-iteration, factorization,
recovery or certification work or retained memory. The new bounded offline
analysis reads two 96x96 factor snapshots, constructs exact sparse L*U products
and matrix-vector products, and stores a fixed row/error ledger. It performs no
new native factorization/solve, Julia compilation or measurement. No allocation
or speedup claim is made. Prior measured timings and allocation counts stay frozen.
