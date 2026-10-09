# Reduce native residual work without numerical changes

Baseline ce84212 / production9c67ab2. Reuse existing isolated worktree.

Investigate CSC transposed compensated residual accumulation first: each column
owns one output component, so local scalar accumulators can replace repeated
scratch-array traffic without changing FMA, TwoSum, zero skipping or summation
order. Retain the generic forward/dense/other-precision paths. Before production
code, add a differential test against the frozen scalar-per-term reference.
Cover Float32/64, zeros, subnormals, cancellation, overflow/nonfinite and sparse
shapes. Compare every scratch component and final acceptance result.

Measure paired warmed kernels on synthetic sparse/dense-in-CSC and saved runtime/
medium bases; count bytes, calls and nonzeros. Proceed only with measured benefit.
Then run targeted numerical tests, broader semantics/external cases and complete
dual runtime with reference fingerprints. Independent correctness/work/memory
review precedes commit and integration under the user's standing authorization.

Second candidate: the post-native-correction caller repeats the row residual
already certified by the correction. Trace stop/observer mutation semantics
before deciding whether to remove this scan; do not assume purity of callbacks.
Further candidates (basis assembly and finite checks) need invalidation evidence;
no global cache or weakened safeguard is part of this bounded change.
