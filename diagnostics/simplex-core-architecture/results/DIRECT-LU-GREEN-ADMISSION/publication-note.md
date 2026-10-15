# Preserved publication refusal and exact source-fidelity exception

The original publication.py executed once and stopped before publication.json,
commit and push: git diff --cached --check returned2 for exactly four trailing
blank lines in unchanged focused test slices (script exit1). Its original bytes,
closure15PASS/39bindings and the staged source slices remain unchanged. The
failure is recorded in publication-failure.json. No numerical attempt occurred.

whitespace-check.py is a separate one-shot check: exact four warning lines,
byte identity to frozen prior focused files, byte identity to the current source
slices, and a clean check for every other path. All four gates passed. This
preserves source fidelity rather than deleting source bytes to satisfy lint.
It is not a blanket whitespace waiver. No candidate, driver, test, count,
manifest, admission or previous review changes.

Separate publication-review.md/json review this exception and new publication
controls. closure-final.py verifies old closure bindings unchanged and the new
review/exception. publication-final.py fixes an exact expanded names/blob list,
requires the existing staged set to equal the known original40 paths and checks
exact warning output and clean other paths again before commit. It exclusively
publishes publication-final.json. Original publication.py is frozen and never
rerun; its nonexistent publication.json is not invented as a successful record.
