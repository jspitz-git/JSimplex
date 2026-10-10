# Measured time budgets

One paired reference and census per slice; sampling completed only for prefixes. A second dual-origin cleanup reference is retained with the stalled attempt. No speedup claim.
All times are seconds. GC is included in wall time. Allocation bytes are cumulative, not peak memory.

| Slice | Steps | Reference | Sampling | Census | Reference GC | Reference allocated GiB | Read / deserialize | Process peak RSS GiB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| medium-dual | 4000 | 60.628 | 108.434 | 59.445 | 17.192 | 10.585 | 5.644 | 3.356 |
| medium-primal | 2000 | 64.194 | 112.370 | 61.537 | 16.944 | 10.039 | 5.503 | 4.200 |
| cleanup-dual | 256 | 87.552 | unavailable | 100.304 | 16.066 | 7.023 | 0.357 | 3.055 |
| cleanup-primal | 256 | 81.412 | unavailable | 89.817 | 9.419 | 4.373 | 0.387 | 3.043 |

Process peaks include loading, warmups, compilation and all completed modes.
All reference/profile/census timed regions report zero compilation (asserted during table generation).
Warmups and complete process timings are retained in each case directory.

## Exclusive census seconds

Columns partition the complete census timer, including setup and observer.
Buckets classify exclusive function bodies, not chronological phases. Basis work includes entry and ordinary solves/refactors; projection_other excludes nested basis work. Weight_updates excludes lazy weight construction inside selection and its nested solves.
Unwrapped work and timer bookkeeping remain in the containing bucket.
The numerical bucket is not the total cost of safeguards: unwrapped checks can remain in iteration/reconstruction buckets.

| Category | medium-dual | medium-primal | cleanup-dual | cleanup-primal |
|---|---:|---:|---:|---:|
| basis | 16.019 | 12.942 | 66.913 | 58.700 |
| iteration_other | 1.978 | 8.980 | 3.339 | 3.540 |
| numerical_checks_recovery | 9.003 | 2.030 | 8.630 | 8.911 |
| observer | 1.522 | 0.793 | 0.174 | 0.172 |
| outer_other | 1.079 | 1.271 | 0.400 | 0.448 |
| projection_other | 0.000 | 0.000 | 8.234 | 5.065 |
| reconstruction | 0.062 | 9.902 | 2.115 | 2.123 |
| selection | 7.751 | 6.322 | 9.959 | 10.327 |
| setup | 15.931 | 16.439 | 0.062 | 0.055 |
| values_and_flips | 4.681 | 0.000 | 0.000 | 0.000 |
| weight_updates | 1.418 | 2.857 | 0.477 | 0.476 |
| Total | 59.445 | 61.537 | 100.304 | 89.817 |

## medium-dual

Reference allocation events: 168,135,257; census: 168,139,254.
Phases: phase_dual at 0 (+0), phase_auxiliary at 0 (+0).

| Function | Calls | Exclusive s | Inclusive s (overlapping) | Exclusive GC s | Exclusive allocated MiB |
|---|---:|---:|---:|---:|---:|
| `presolve_problem` | 1 | 15.374 | 15.374 | 9.196 | 7794.058 |
| `_pipeline_basis_solve!` | 16,032 | 10.161 | 10.161 | 0.000 | 0.000 |
| `_finite_workspace` | 16,004 | 4.589 | 4.589 | 0.000 | 0.000 |
| `refactorize!` | 12 | 4.169 | 4.169 | 3.753 | 2480.021 |
| `_bound_flipping_ratio_test` | 4,000 | 3.310 | 3.310 | 0.000 | 4.177 |
| `price!` | 4,000 | 2.936 | 2.936 | 0.000 | 0.000 |
| `_apply_bound_flips!` | 4,000 | 2.763 | 5.215 | 0.000 | 0.000 |
| `_dual_direction_residual_ok!` | 4,000 | 2.609 | 2.609 | 0.000 | 0.000 |
| `_dual_iteration_unchecked!` | 4,000 | 1.978 | 40.239 | 0.000 | 0.183 |
| `_dual_row_residual_ratio` | 4,000 | 1.801 | 1.801 | 0.000 | 0.000 |
| `_replace_pivot_column!` | 4,000 | 1.662 | 1.662 | 0.000 | 0.309 |
| `observer` | 16,016 | 1.522 | 1.522 | 0.000 | 0.857 |
| `dual_edge_selection` | 4,000 | 1.500 | 1.500 | 0.000 | 0.000 |
| `update_dse!` | 4,000 | 1.411 | 3.957 | 0.000 | 0.000 |
| `update_duals!` | 4,000 | 1.267 | 1.267 | 0.000 | 0.000 |
| `outer_unattributed` | 1 | 1.079 | 59.445 | 0.000 | 223.192 |
| `update_primals!` | 4,000 | 0.650 | 0.650 | 0.000 | 0.000 |
| `initialize_workspace` | 1 | 0.557 | 0.561 | 0.521 | 317.171 |

After excluding the first window (which includes setup), the 30 full 128-step windows have median 9.458 ms/step, range 8.796–12.814 ms/step. These are windows of one trajectory, not independent repetitions.

## medium-primal

Reference allocation events: 168,120,504; census: 168,120,501.
Phases: phase_one at 0 (+0).

| Function | Calls | Exclusive s | Inclusive s (overlapping) | Exclusive GC s | Exclusive allocated MiB |
|---|---:|---:|---:|---:|---:|
| `presolve_problem` | 1 | 15.139 | 15.139 | 8.963 | 7794.294 |
| `recompute!` | 2,003 | 9.902 | 15.487 | 0.000 | 0.000 |
| `_pipeline_basis_solve!` | 10,006 | 9.418 | 9.418 | 0.000 | 0.000 |
| `_primal_iteration_unchecked!` | 2,001 | 8.980 | 43.128 | 0.000 | 41.343 |
| `_primal_update_steepest!` | 2,000 | 2.857 | 6.513 | 0.000 | 0.000 |
| `price!` | 4,000 | 2.828 | 2.828 | 0.000 | 0.000 |
| `refactorize!` | 7 | 1.983 | 1.983 | 1.762 | 1449.564 |
| `_primal_ratio` | 2,000 | 1.951 | 1.952 | 0.000 | 0.000 |
| `_primal_entering` | 2,001 | 1.543 | 1.543 | 0.000 | 0.000 |
| `_replace_pivot_column!` | 2,000 | 1.530 | 1.530 | 0.533 | 129.752 |
| `initialize_workspace` | 2 | 1.301 | 1.309 | 1.162 | 638.820 |
| `outer_unattributed` | 1 | 1.271 | 61.537 | 0.538 | 215.011 |
| `_dual_row_residual_ratio` | 2,000 | 1.007 | 1.007 | 0.000 | 0.000 |
| `observer` | 6,012 | 0.793 | 0.793 | 0.000 | 0.367 |
| `_finite_workspace` | 2,001 | 0.641 | 0.641 | 0.000 | 0.000 |
| `_legacy_primal_direction_price_ok` | 2,000 | 0.380 | 0.380 | 0.000 | 0.000 |
| `_basis_matrix!` | 7 | 0.012 | 0.012 | 0.000 | 9.197 |
| `_primal_bound_snap_feasible` | 4,000 | 0.001 | 0.001 | 0.000 | 0.000 |

After excluding the first window (which includes setup), the 14 full 128-step windows have median 20.282 ms/step, range 18.512–32.863 ms/step. These are windows of one trajectory, not independent repetitions.

## cleanup-dual

Reference allocation events: 2,780,762; census: 2,780,762.
Phases: phase_cleanup at 212280 (+0), phase_primal at 212280 (+0).

| Function | Calls | Exclusive s | Inclusive s (overlapping) | Exclusive GC s | Exclusive allocated MiB |
|---|---:|---:|---:|---:|---:|
| `_pipeline_basis_solve!` | 19,696 | 44.833 | 44.833 | 0.000 | 0.000 |
| `refactorize!` | 16 | 21.409 | 21.409 | 20.153 | 5944.655 |
| `_primal_entering` | 257 | 8.407 | 44.987 | 0.000 | 0.000 |
| `_project_postsolve_basis!` | 1 | 8.234 | 32.223 | 6.073 | 533.874 |
| `_primal_iteration_unchecked!` | 257 | 3.339 | 66.083 | 0.402 | 67.179 |
| `_restore_legacy_primal_point!` | 256 | 2.671 | 7.254 | 0.000 | 0.000 |
| `recompute!` | 259 | 2.115 | 8.143 | 0.000 | 9.632 |
| `_primal_row_bounds!` | 259 | 2.068 | 2.068 | 0.000 | 0.000 |
| `_dual_row_residual_ratio` | 256 | 1.073 | 1.073 | 0.000 | 0.000 |
| `_legacy_primal_model_feasible` | 256 | 1.046 | 1.474 | 0.000 | 0.000 |
| `_primal_ratio` | 256 | 1.029 | 1.029 | 0.000 | 0.000 |
| `_legacy_primal_row_consistent` | 256 | 0.693 | 0.694 | 0.000 | 0.000 |
| `price!` | 512 | 0.523 | 0.523 | 0.000 | 0.000 |
| `_basis_matrix!` | 4 | 0.504 | 0.504 | 0.470 | 57.997 |
| `_primal_update_steepest!` | 256 | 0.477 | 1.350 | 0.000 | 0.000 |
| `_native_primal_rows_filter` | 515 | 0.434 | 0.434 | 0.000 | 17.915 |
| `cleanup_original` | 1 | 0.399 | 100.303 | 0.000 | 16.335 |
| `_finite_workspace` | 516 | 0.285 | 0.285 | 0.000 | 0.000 |

After excluding the first window (which includes setup), the 1 full 128-step windows have median 85.389 ms/step, range 85.389–85.389 ms/step. These are windows of one trajectory, not independent repetitions.

## cleanup-primal

Reference allocation events: 4,347,786; census: 4,347,786.
Phases: phase_cleanup at 335046 (+0), phase_primal at 335046 (+0).

| Function | Calls | Exclusive s | Inclusive s (overlapping) | Exclusive GC s | Exclusive allocated MiB |
|---|---:|---:|---:|---:|---:|
| `_pipeline_basis_solve!` | 18,698 | 44.937 | 44.937 | 0.000 | 0.000 |
| `refactorize!` | 9 | 13.088 | 13.088 | 12.309 | 3374.238 |
| `_primal_entering` | 257 | 8.671 | 47.484 | 0.000 | 0.000 |
| `_project_postsolve_basis!` | 1 | 5.065 | 18.309 | 3.436 | 386.653 |
| `_primal_iteration_unchecked!` | 257 | 3.540 | 69.392 | 0.426 | 67.179 |
| `_restore_legacy_primal_point!` | 256 | 2.801 | 7.358 | 0.000 | 0.000 |
| `recompute!` | 259 | 2.123 | 8.405 | 0.000 | 9.632 |
| `_primal_row_bounds!` | 260 | 2.092 | 2.092 | 0.000 | 0.000 |
| `_dual_row_residual_ratio` | 256 | 1.226 | 1.226 | 0.000 | 0.000 |
| `_primal_ratio` | 256 | 1.147 | 1.147 | 0.000 | 0.000 |
| `_legacy_primal_model_feasible` | 256 | 1.034 | 1.459 | 0.000 | 0.000 |
| `_legacy_primal_row_consistent` | 256 | 0.684 | 0.684 | 0.000 | 0.000 |
| `_basis_matrix!` | 4 | 0.515 | 0.515 | 0.481 | 58.258 |
| `price!` | 512 | 0.509 | 0.509 | 0.000 | 0.000 |
| `_primal_update_steepest!` | 256 | 0.476 | 1.375 | 0.000 | 0.000 |
| `cleanup_original` | 1 | 0.446 | 89.816 | 0.000 | 16.335 |
| `_native_primal_rows_filter` | 516 | 0.433 | 0.433 | 0.000 | 22.413 |
| `_finite_workspace` | 516 | 0.275 | 0.275 | 0.000 | 0.000 |

After excluding the first window (which includes setup), the 1 full 128-step windows have median 89.402 ms/step, range 89.402–89.402 ms/step. These are windows of one trajectory, not independent repetitions.
