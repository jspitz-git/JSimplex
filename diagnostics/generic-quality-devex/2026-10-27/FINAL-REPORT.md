# Integrated BigFloat residual, quality and Devex savings

Production commit `ca64312f7f74b1d7bec047718399f229674b3e1d` is integrated and remotely verified on origin/master. Five reviewed files, all source inverses exact. All numerical safeguards/tolerances/rounding/precision/input owners/fallbacks preserved; no new scan/solve/copy/persistent cache. Independent review found no unnecessary production work or retained numeric memory.

| Complete function | Across-cell median candidate/original time | Observed BF byte savings |
|---|---:|---:|
| Dual direction / row residual | 0.9537 / 0.9163 | about0–26.4% |
| Normal / transposed solve_quality! | 0.7557 / 0.7580 |14.8–41.2% |
| Devex shared / actual BTRAN+price |0.5634 /0.8766 |42.3–61.7% /12.6–29.6% |

One process/170.614s/33807PASS/1160cells20880windows. Cold/warm/setup/snapshots/reset costs separate; all measured compile/recompilezero and all490GCwindows/outliers retained. Residual gain depends on sign. All three slower quality timing cells (1.1344,1.1114,1.0122) remain disclosed; no universal/end-to-end speedup claim. Native/exact control events identical;15Rat medianbyte differences retained without cause attribution. See MEASUREMENT-REPORT.md, RESULT-REVIEW.md and raw output/results.toml.

RED9465PASS+6expectedwholecallcostfailures; GREEN 186622PASS/1533.552s; actual MASTER 186622PASS/1500.478s. Each complete34ordinaryfiles, no errors/broken/skips/customrecorder/manualTeststack. All original tests and3percent thresholds unchanged. All reviews independent, actualcommit verified before ff-onlyintegration, actualmaster passed before normalnonforcepush.

Earlier7e306e24 historical failed allocation gate and its once-only human exception remain unchanged, not relabeled or proved fixed. No reuse of that exception here. Fullsuite/x64/broaderplan/native-memory/end-to-end remain open. CIoff/automationpaused/HHreuse disabled. Protected userfiles/env/unrelatedindexes and all old raw/rejections/maps preserved. Exact old continuation bytes stored in continuation-before and mapped by historical-path-map.json.
