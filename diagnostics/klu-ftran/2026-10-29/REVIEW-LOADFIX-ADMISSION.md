# Independent loading correction and distinct second-attempt admission

**Accepted: one distinct comparison-2 guarded attempt of the same fixed diagnostic, shared ceiling <=1800 seconds, conditional on fresh launch-pins-2.json and an immediately preceding host check. No Critical or Important finding remains in this narrow correction.** The first launch and its consumed admission remain frozen. This is separate admission under the user's standing request to try FTRAN, not reuse of the original no-retry permission or acceptance of the failed attempt as numerical evidence. No further retry, workload increase or numerical-policy change is authorized here.

I independently read comparison-1/guard/run.log, process.json, supervisor.json and postflight.json. The log reports ParseError at candidate.jl:145 for ambiguous `-1./p.Rs[pos]`, reached through driver.jl:4's include. main is defined and called later, so it never ran: no factor preparation, microtests, captured input loading or measurement occurred. The absence of results-1.toml agrees. Definitions/import/runtime initialization before that include may have executed; this was a loading failure, not a numerical-test result. Recorded child/guard duration is2.144167601s; supervisor duration2.329967518s, accepted=false; reason exit1, returncode1, pins_unchanged=true. Postflight checks717 historic/new groups and sessions, with no Julia/group/session conflict. The prior static review missed this parse ambiguity; the correction is required before the unchanged experiment can load.

All **58/58 original launch inventory files** independently retain their exact resolved path and SHA-256. Original launch-pins.json SHA-256 is `cd2971ce706e9dada1b6b5261275af66ecfeb3dca94fc1f64141dba33b087305`. No old source, raw failure, result, guard or review artifact was modified by this review. Complete hash evidence is REVIEW-LOADFIX-BINDINGS.json.

Exact new-source comparison was checked mechanically as well as visually:

- candidate-loadfix.jl equals candidate.jl after exactly one replacement, `-1./p.Rs[pos]` to `-1.0 / p.Rs[pos]`. This explicitly spells the existing intended Float64 negative-one scalar division. No operator, index, order, guard, threshold, test expectation or precision changes.
- driver-loadfix.jl differs only in the included candidate filename.
- command-2.json retains the complete launcher/runtime/options/project prefix; only driver and fresh results filename change.
- verify-loadfix.py equals verify.py after replacing only results/comparison/launch-pins/samples/analysis names with their attempt2 names. Python AST parsing succeeds; no auditor semantics change.
- Neither new Julia source has another integer-followed-by-dot-arithmetic-operator sequence under a focused static pattern check. This is a bounded source check, not proof of complete Julia parse/runtime success. No Julia/import/query/native numerical work was executed by this reviewer.

Current SHA-256 bindings:

- candidate-loadfix.jl: `1f83850b83cbfae4564f17509c95e0b7b306b359a2dad051bf182871f3eecc2a`
- driver-loadfix.jl: `7e1d77d6bced0d5c44f302eef0c029cf9d33ce34705e67484b885de89910e8dd`
- verify-loadfix.py: `0b4b5a14bd334d8b5f544e892c5af0d92c83237967a7de442b0c4650d00ef4ef`
- command-2.json: `7f4235bc1f3b6a8d1e77f9deab7baf734dd79265cba91e20317460202b463a38`
- LOADFIX-ADMISSION.md: `30d6d8990d77edf43d38ee186ed8473c82cc84b1f90a19cfa2a9e17e921f6ab3`

The accepted prior numerical/alias/lifetime/work and memory assessments apply unchanged to these new source bytes. All12 cases/489 queries per cycle,58680 measured whole calls, warm/cold/microtest schedule, residual/directed-enclosure/relative checks, allocation/compilation observations, thresholds and frozen input history remain unchanged. The two attempts do repeat loading/import overhead, but no previous factorization/query/measurement is repeated because none ran. **No unnecessary NEW production work or retained-memory cost was introduced: there is no production-code change.** This syntactic correction adds no per-call computational work, allocations or retained memory. Existing native/export duplication, dense preparation/scatter passes, heap/bookkeeping, fallback sunk work and exported-only counters remain fully chargeable and must be reported.

A fresh independent review-time /proc snapshot checks the same717 groups on the same boot, no Julia/group/session conflicts, available22683372KiB and swap0. REVIEW-LOADFIX-CHECKS.json records exact-diff and host evidence. This snapshot is not the required immediate prelaunch check.

Concrete distinct admission: bytecode-disabled Python runs `run.py comparison-2 command-2.json launch-pins-2.json 1800 0` (or smaller shared ceiling), after freezing/validating a fresh manifest including all current new files, this review, immutable first-failure evidence and the unchanged guard/runtime/input dependencies. A fresh host check must include all717 historic groups AND sessions, new records if any, refs, boot and memory. Existing sole-owner lock, one Julia/BLAS thread, existing compiled modules, heap hint2GiB, VM8GiB, availableRAM>=6GiB/swap<=1GiB, identity publication gate/parent-death signal and PIDFD cleanup remain required. Accept comparison-2 only after ordinary Test success, full numeric/count/compile/library/pin verification, complete postflight closure and independent result/work/memory review. No numerical result, speedup or production integration is admitted by this document.
