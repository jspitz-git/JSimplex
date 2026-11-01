# Deferred whole-branch Minor findings

1. Existing Task1 setup: inverse=zeros(Int,N), then _basis_inverse! fills it with zero again. This is one extra cold N-entry zeroing pass, no retained-memory increase. Previously disclosed and unchanged in Task6.
2. Newly noticed in final review of existing Task4 recovery.jl::_repair_target!: all(isfinite,q.values) visits m entries, then _capture_output! repeats finite checks while capturing the same successful correction output. One extra m-entry pass on the recovery path, not every ordinary pivot; no extra retained buffer. All Task6 timed/cold main-phase correction counters are zero, so this is not an observed explanation of Task6 slowdown.

Both are nonblocking performance findings with safeguards preserved. Defer them under the frozen-source/no-tuning measurement contract; no code, tolerances, inputs, old results or accepted launch pins change. Removing the second prepass later must preserve failure/exception/proof-publication behavior and have its own targeted tests and concrete numerical admission. These notes are not a claim of general cost equivalence or measured benefit from a hypothetical fix.
