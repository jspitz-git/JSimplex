# S4-C independent final review

Reviewer: fresh gpt-6-astra subagent, read-only, no numerical runs or edits.
Decision: approved for bounded integration subject to the planned master gate.
No blocking, numerical correctness or deferred minor findings.

Count/fill agreement holds: packed index/value lengths are maintained together;
dense count/fill predicates and ordering match. Stored sparse zeros, tiny entries,
permutations, scalar types and CSC accumulation order remain unchanged. Frozen
reference independently matches prior production. Shared one(T) matches former
fill semantics. Outputs remain independently constructed/owned.

No unnecessary work or retained-memory increase found within the chosen exact
allocation approach. Two length reads per sparse pivot plus one core predicate
scan add O(k+c²) setup/refactorization work, including recovery refactorization.
No update-chain dependence, new retained cache, dense copy, conversion or solve.
Six exact temporary vectors eliminate dynamic growth/copy traffic.

Evidence inspected: GREEN442, focused4366,84compile0cost samples/14audit gates,
8exact trajectory pairs/121assertions/9audit gates; source hashes and paired
records independently checked. Dense256 bytes per16 calls117710080 ->59285632;
events2640 ->1200. Mostly-zero256 side-median1.0258/paired-median1.0088 is an
acknowledged counting-pass tradeoff/uncertainty; small/mixed timings are noisy.

Declined claims: whole-solver speedup, large-core/cross-precision cost, full-repo
correctness and whole S4/S5/S6 completion. These remain open scope, not waived
gates. Author ruling: retain these limits; no wider claim or numerical bypass.
