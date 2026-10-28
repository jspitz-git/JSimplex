# Independent original-source RED admission

Accepted, findings none, for one RED attempt only. The independently frozen ordinary Test outcome is **7258 total =7252 passes +6 allocation failures**, each at RED/test/generic_residual_pivot_crash_tests.jl:409. Expected child exit1. Any additional failure, changed location, compilation failure, error, skip/broken test, wrong total or resource failure invalidates RED. No Julia, parser/query/import/compile/native call, old script or numerical workload was executed by this review.

## Exact test and stage

RED contains exactly the542 preserved baseline files plus the single new test (543 total). Every baseline file matches both the baseline snapshot and actual master, including all production source, old tests, Project, Manifest and LocalPreferences. The test bytes exactly match new-test.jl. Its prefix is exactly the unchanged full Reference module followed by RPCA/RPCB/RPCC aliases to the actual loaded JSimplex and unchanged fixtures-final.jl; the new suffix supplies only six fixed allocation gates and the ordinary test root. No candidate module is substituted for production. No original test or threshold was changed. The driver asserts actual package source and active project point to RED and includes only the new test.

The ordinary correctness loops are identical to the successful private comparison:7174 assertions across15 BigFloat precision/rounding contexts plus Float32/Float64/Rational BigInt/Rational Int64. The six gates each run checkpair (6 assertions for residual,8 for update,7 for crash),3 warm pairs, then3 alternating measured pairs with6 compile/recompile-zero assertions, and one joint cost assertion. Thus gate totals are2*13 +2*15 +2*14=84, yielding7258. The six final assertions require lower event counts in every pair AND lower median bytes; there is no timing threshold. Original source reproduces the Reference work, so these six improvements are the only expected failures; all correctness and compilation assertions must pass. This remains an expected outcome to verify from raw RED output, not a claim that RED has already passed.

The concrete gates are A BigFloat sparse n64 positive structural/slack residuals; B BigFloat sparse n16 positive new/recycled whole PFI updates; C dense n32 mixed cap8 crash selection for BigFloat and Rational BigInt. Every gate matches exactly one saved BF128Nearest or Rational BigInt comparison cell. All nine saved event ratios are lower and the byte medians are lower in those cells. The candidate result review independently matched those savings to removed work. Fixed3 pairs preserve a meaningful regression gate without turning timing noise into a correctness failure.

## Numerical/work review

The added test invokes the full affected functions; preparation/reset/result capture occurs outside the timed function. It retains ordinary expected results, exact cutoffs, owner/precision/context checks, recycled-buffer identities and real forward solve coverage. No numerical guard or arithmetic tolerance is weakened. New tests add test-only setup and comparisons; production source is unchanged, so there is no new production execution work or retained-memory cost in RED. Native allocation retention is not established by these Julia allocation counters.

The original Reference duplicates narrowly selected function bodies for independent comparison and requires intentional upkeep if later semantics change. Its imported types/helpers are the actual package's unchanged shared facilities; numerical candidates in this stage are actual original JSimplex. Reference and fixture bytes are explicitly bound.

## Controls and expected-output audit

The canonical command is contract.json in this RED-run directory, through launch.py/common.py and the unchanged reviewed guard. Limit is3600 seconds inclusive, guard deadline3592, single Julia/BLAS threads, GC1,0, existing compiled modules,2GiB heap hint,8GiB AS, availableRAM>=6GiB and swap<=1GiB. There is no reservation/output yet and only one attempt is admitted.

The root phase-audit.py is bound by this admission and included in the1328 manifest. Its intended postexit copy RED-run/audit.py must be byte-identical so `from common import *` resolves RED-run/common.py. This supplemental copy is not retroactively claimed as an entry in the original1328 launch manifest. The auditor requires ordinary Pass/Fail/Total/Time with exactly6 failures at the six line409 locations, no test errors/broken/skips, the admitted7252 passes/7258 total, ordered single file include, source identity, owned startup/command/pin links, resource bounds and completed inclusive deadline. Its contract expected_total is null, but its explicit admission.json checks enforce the independently frozen exact totals.

## Independent current verification

All1328 RED inventory hashes/resolved paths/tree memberships and all1251 original,1268 READY,1285 final comparison manifests were verified. The accepted result-review bindings are unchanged. Exact baseline/test composition, guard equivalence, launch budget substitutions and all six saved gate cell matches passed. Actual/local/tracking/live master remainsbb765d008c6e8aab6187aa0ea49d49a4f8a03309; diagnostics local/live remains94394f8b91a4670c24f7fb9e7c23c468e4cadfd4.

Fresh admission-evidence.json contains the full661 historical/current groups AND sessions scan with exact boot/start_ticks/command identities, no active Julia, available-memory/swap checks and only the fixed hash-bound WSL allowance. Protected user files/indexes and inherited environment remain unchanged. Every canonical file and the expected postexit auditor digest are bound in admission.json. This admission does not authorize or certify any later production stage, GREEN, MASTER, commit or publication.
