# Triangular update kernel performance

Work in `fix/triangular-update-kernels`, based on `17be8a3`. Commit each verified change separately. Keep native precision, tolerances, pivot selection, and refactorization policies unchanged. Do not investigate allocations.

1. Establish the numerical baseline and measure FT/SS update stages on identical recorded runtime.mps exchanges. Capture an additional diagnostic prefix through the late FT slowdown. Keep serialized histories local.
2. Remove repeated packed-column edits during FT/SS row elimination. Extract the moved row into existing scratch, rotate the remaining row indices once, perform elimination in scratch, and restore the completed row once. Preserve zero normalization and arithmetic order. Verify the row transformation independently before implementation, then compare complete updates with the previous implementation.
3. Measure replacement and solve costs on identical real histories at 20, 80, 160, and 320 updates. Retain changes only with measured benefit and unchanged numerical results. Use late histories to distinguish kernel cost from changing basis structure.
4. Run factorization and hypersparse regression checks and external LP corpus validation. Attempt an adequately budgeted runtime.mps solve if diagnostic results justify it; report prefixes and time limits explicitly.
5. Obtain a read-only review, document remaining structural costs and practical limits in English, and commit verified work. Integration is a separate user action.

Resource limits: one numerical Julia process at a time, 24 GiB virtual memory. Never solve big.mps, largo.mps, or AnyMod.mps. Do not modify or signal editor processes.

## Measured design revision

The moved-row scratch prototype preserved every tested coefficient but did not
improve timings consistently, even after bounding the index-shift loop. It is
not retained. Initializing the same update representation directly from the
backend LU also failed to improve timings; a direct-LU design would require
more than substituting the initial factors.

The selected implementation reuses the pre-upper-solve spike produced by a
recent FTRAN. Two private slots accommodate the intervening steepest-edge
FTRAN. A slot is usable only for the identical output buffer with exactly
unchanged values, in the same unmodified basis, and finite native floating
values. Refactorization and updates invalidate all slots; copies start empty.
Corrected, external, or arbitrary-precision directions use the original
reconstruction. Unlike the rejected row-storage prototype, this avoids a full
upper-factor multiplication and changes rounding, so validate numerical
quality and full solver behavior, not exact old/new coefficients.

On a preliminary 320-exchange replay at runtime iteration 40097, this reduced
replacement time by 35–41% across the three managers with small solve residuals.
This does not establish a full-solve speedup or parity with PFI.

## Verified implementation

Committed as `99ba627`. Final recorded-exchange measurements reduce runtime
replacement costs by 31–50%, or 23–31% including two FTRANs. Medium's recorded
early history improves by 20–26%, or 13–14% including FTRANs. Numerical replay
checks pass through 320 updates for all three managers and the PFI control.
The row-scratch and direct-LU prototypes were rejected on measured performance.
See `diagnostics/triangular-update-kernels/README.md` for evidence and limits.

The implementation also guards provenance against overlapping output views,
BTRAN/indexed solves, and pipeline copy paths. Final targeted coverage totals
19,895 assertions. Full-solver and full-suite outcomes are recorded with the
final diagnostics rather than inferred from kernel timing.

Final full FT validation completed runtime.mps OPTIMAL in 844.240 seconds and
62,939 iterations, with original-input feasibility and prior PFI objective
agreement. The full test suite did not complete in 900 seconds; its timeout
stack was in LLVM optimization at partial_pricing_edge_tests.jl. This limitation
is recorded explicitly, alongside successful targeted and external checks.
A requested read-only comparison with Simplex.jl identified eta-based ordinary
FT/BG managers, actual BGTransform, and candidate stable-index mechanisms;
BGTransform is not adopted as a replacement.
