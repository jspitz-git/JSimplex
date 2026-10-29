# Native Float32/64 quality experiments

Base: 235eedf33901fe8c4cc06a3d8c3508ef2fcbb718. Excluded prior ABC optimizations remain excluded.

Compare the whole solve_quality! independently for A (existing SIMD finite scans), B (local integer term counter in ordinary transposed CSC accumulation), and AB. Original numerical products, residual/scale order, tolerance, underflow checks and fallbacks remain. B rejects byte overlap with every loop-accessed array; try/finally preserves partial counters after invalid indexing. Unsupported arrays/types stay generic.

Use ordinary Test testsets and warm alternating paired measurements (12 measured pairs; all times, GC traffic/events, compilation separated). Float32/64, sparse3/sparse15/dense, 16/128/384 dimensions, FTRAN/BTRAN, finite correct and incorrect solutions. Edge correctness: zero/subnormal/nonfinite/extreme values, empty/rectangular, explicit zeros, alias rejection, invalid CSC partial scratch. Compare all scratch and inputs as well as quality fields and exception types. No LP files; one Julia at a time, 1 Julia/BLAS thread, 2GiB heap hint, 8GiB VM, 6GiB available RAM minimum, 1GiB swap maximum. Each process bounded by 1800s to allow compilation; measured work is short. No performance claim from output correctness or counts alone.

Only measured beneficial variants with no allocation increase, unchanged safeguards and fresh independent review may enter production. Then run ordinary permanent/regression tests in isolated candidate and master before push; preserve all failed results. No old scripts executed or old evidence rewritten.
