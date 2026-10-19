# Final counter-schema supplement

The intermediate independent correction review remains rejected and frozen: 8,150 checks, 23 malformed final-counter acceptances, all 21 original findings repaired. The final top-level probe `counts` dictionary was compared to its last checkpoint by value; equivalent floats or Booleans could compare equal without passing the strict checkpoint counter validator.

The separate final change adds exactly `counters(v['counts'])` at `probe_ok` entry. No Julia driver, candidate, probe, stage, guard, supervisor, outer or launch source changes. It adds 13 fixed cold counter checks per completed probe (eight probes total), outside the measured process. No additional solve, factor copy, Julia allocation or retained production memory.

`count-fix-check.py/json` independently exercises detached dictionaries: all 13 equivalent floats and ten zero-valued Booleans reproduce the old acceptance and are rejected by the new code; negatives, infinities, strings, nulls, missing/unknown keys also reject. 5,364 checks pass, including exact initial and intermediate bindings. This is offline Python validation, not Julia qualification.

`control.py.before-count-fix` and `evidence.py.before-count-fix` preserve the exact intermediate bytes. `count-fix-map.json` maps only intermediate 2,594-path manifest and intermediate author/review bindings. The earlier three `.before-review` mappings are unchanged. Both rejection reports, checkers, raw failures and manifests remain intact and are never rerun or rewritten.

Canonical future preparation uses `preparation-pins-final.json`, `required-paths-final.json`, and accepted `review-final.json`; the prior reviewed manifest remains historical. `closure.py` and `closure-final.py` are unexecuted preserved drafts; `closure-complete.py` is the separate final closure. This supplement takes precedence over intermediate canonical filenames in REVIEW-FIX.md. No launch admission or numerical allowance is created by this preparation.
