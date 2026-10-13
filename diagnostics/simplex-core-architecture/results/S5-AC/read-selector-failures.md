# Preserved read-only selector mistakes

Three exploratory rg calls named absent files. These are source-path lookup
mistakes, not Python evidence failures, Julia runs or numerical counterexamples.
The full outputs remain in the task transcript. No file was created by these reads.

1. src/simplex_factorization.jl, src/simplex_pipeline.jl and
   src/simplex_refactorization.jl: No such file or directory (os error 2).
2. src/product_form_inverse.jl and src/basis_factorization.jl:
   No such file or directory (os error 2).
3. test/native_cleanup_primal_transition_tests.jl and test/unscaled_certificate_tests.jl:
   No such file or directory (os error 2).

Subsequent rg --files identified actual src/factorization.jl,
hypersparse_pipeline.jl, refactorization_policy.jl and test/unscaled_cleanup_tests.jl.
No absent path contributes a binding or an execution-coverage claim.
