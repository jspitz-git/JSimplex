# Initial finalization preparation review

Not accepted: one pre-write protection gap. Exact file bindings are in the companion JSON.

`finalize.py` checks the original master-index beforeimage, but does not directly check all current indexes against `MASTER-run/protected-before.json` or every current protected file against `protected-before.json` before its first write. Generic independent-review bindings do not enforce complete coverage. `closure.py` checks these states only after finalization has prepared artifacts and prepended continuation text. Add explicit current protected-file and index checks before any `put`, `mkdir`, copy or write, while retaining original beforeimage validation.

Other static checks passed: correct fresh-case paths and direct all-pass audit schema, six historical/current pin sets, exact source/index/continuation maps, initial rejected-admission preservation, final review/PASS closure gates, exact diagnostic names/blobs/parent and normal remote-verified push. Python syntax is valid. This is preparation review only; no controls or Julia were executed, no author controls or production/Git state were changed, and no host check was performed during the active comparison. Cold certification scans are justified; no unnecessary numerical work or retained solver memory is introduced. Actual production and results remain unaccepted by this review.
