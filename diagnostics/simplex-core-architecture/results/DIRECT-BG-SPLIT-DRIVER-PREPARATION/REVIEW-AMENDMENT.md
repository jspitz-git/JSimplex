# Preserved initial review and bounded ledger correction

Initial review R1 found an incomplete test-only work bound. The partition traversal is O(n+C+R+K), but `_sbu_check` also constructs two n-entry Int vectors and sorts them, with invariant bookkeeping allocations. The corrected field states those additional costs and makes no overall linear or measured-allocation claim.

Only `work-ledger.json` is corrected. Candidate, tests, driver, numeric counts and source-derived callback counts are unchanged. Original `derive-counts.py` remains frozen and its emitted ledger field is superseded by this amendment; it is never rerun. The original source-check.json work-ledger binding maps ONLY to work-ledger.json.before-review. All its other bindings remain current. Initial preparation-pins.json maps work-ledger.json to its before-review file and required-paths.json to required-paths.json.before-review; other original pins remain current. Initial review's preparation-pins.json binding maps ONLY to preparation-pins.json.before-review. These mappings apply only on exact hash equality.

Current required-paths/preparation-pins include the corrected ledger and these three preserved originals, this fix script/result and amendment. This is offline preparation, not a launch pin or numerical admission. No Julia, seal, reservation, run or old checker execution.
