# Author review: BG export/import specialization plan

This is a planning-only continuation of the accepted allocation provenance at diagnostic commit `39beb6ff4a9f287dbbfc4c2a3b821d47ce374d0d`. The new specification and plan select a separate namespace with single-body positional cores and thin keyword facades. They do not implement a candidate or execute Julia.

The accepted profile locates extra heap objects at export/build/import boundaries. It does not establish the compiler inference decision responsible for them. Explicit specialization and bounded inlining are therefore a falsifiable candidate design, not an established performance fix. The prior workspace candidate remains rejected for performance, and all prior raw data and anomalous observations remain unchanged.

No unnecessary algorithmic work or retained memory is introduced by the proposed source transformation: array requests, numeric operations, scans, validation, factor ownership, publication and cache policy are required to remain identical. This conclusion is prospective. Compiled specializations may increase preparation time and code memory; cold process observations and the same warmed cost gates remain mandatory. A reduction of boxed helper results alone cannot qualify the candidate.

The new offline source check passed 19 checks with 185 read-time bindings. It also verified the previous accepted result and publication bindings and the frozen profile launch inventory. These are documentary checks, not parser, dispatch, correctness, allocation or timing results for a new candidate. Task1 must use the corrected GREEN2 import test from `diagnostics/direct-bg-export-workspace-harness-fix/reproduce/import-tests.jl`, bound by the actual driver include and sealed inventory. The original lifecycle test is unchanged; the older unfixed import test remains preserved.

The next deliverable after independent acceptance is Task1: a separate candidate, adapted tests, three new boundary tests and exact source inverses, still without Julia. Subsequent RED/GREEN and cost stages require concrete drivers, budgets and independent admission. Standing short-run authorization is preserved; the current deliverable grants no automatic launch or production integration.

Master, production source, permanent tests, environment, CI, STATUS and roadmap are unchanged. Existing untracked user files are preserved. The fresh host record covers the prior 256 process groups and sessions with no matching Julia process; its executable-link visibility limitation is retained explicitly.
