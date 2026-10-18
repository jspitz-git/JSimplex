# Subprocess environment review

Accepted: True. The refusal differs only in PATH session prefixes. All five subprocess tools resolve to the identical files and hashes under current and pinned PATH; HOME and every pinned Julia/loader variable agree. The unchanged seal validates environment before creating the run directory, and that directory is absent. The wrapper executes Julia by absolute path, reads its depot source by absolute path, and controls Julia/BLAS threading explicitly.

Restore only PATH in a copied subprocess environment for the unchanged seal and later authorized launcher. This restores the accepted environment; it does not modify any persistent environment or weaken validation. Fresh exact sealed-stage admission remains necessary.

No unnecessary computational work or retained memory is introduced: the adjustment affects subprocess setup only and adds no numerical operation, vector scan, basis solve, copy, or retained solver object.

Evidence and individual checks are in environment-review.json. No seal, launcher, Julia, package import, compiler, or numerical auditor was executed.

The concrete scoped-entry.py source is inspected and hash-bound. It enforces unchanged non-PATH values, uses absolute /usr/bin/python3 -B and literal cost1-300, creates an exclusive action log, and neither chains seal to launch nor retries.
