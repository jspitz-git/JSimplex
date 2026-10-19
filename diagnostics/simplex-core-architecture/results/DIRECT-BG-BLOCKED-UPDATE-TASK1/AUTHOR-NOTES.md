# Task1 author rulings and preparation record

User authorizes offline Task1 implementation/test text, not Julia. Tests were written before panel.jl; original tests-first bytes and initial author versions are preserved. No RED/GREEN execution or runtime pass is claimed. New Python text/hash checks are not a Julia parser or a mathematical simulation.

Task1 exports standalone helpers. Task2 must retain original prepare/begin/incidence/spike/column rotation and scalar suffix, latch first rejection for rest of update, preserve the two prepared RHS owners and append chronological active steps once. Task1 never starts a solver/factorization or appends history. Zero-operation step slots must be skipped on final history append; b scratch slots are bounded rather than a growing ledger. Whole-update busy/rollback/copy/refactor tests belong to Task2.

The workspace temporarily binds the upper-vector owner to prevent committing into a different factor. It releases that reference on commit/rejection. On a gather/exception failure Task2 must discard the workspace; no independent copy of source arrays is retained. A scalar source mutation between gather/commit is forbidden by the Task2 exclusive-update contract, not detected by an O(nnz) rehash.

A source review caught fixture-only mistakes before any Julia execution: missing LinearAlgebra.I import, immutable structural carrier, and an uneliminated subdiagonal in earlier columns when preparing r>1. These have separate preserved originals. Reservation/writeback exceptions now clear eligibility and release the workspace through the same try/finally. No plan/gate relaxation.

No baseline Julia setup/test is run because the explicit no-Julia request supersedes generic skill setup/TDD execution. Future admission must execute these tests before runtime acceptance. Existing linked diagnostic worktree reused, master/source/test/env/CI/global continuation untouched. No production-cost finding is inferred from source counts alone.
