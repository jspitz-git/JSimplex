# MA-O repaired selective presolver qualification

Date 2026-10-14. **Correctness qualification passed; performance proposal NOT
ACCEPTED. No production integration.** Three new guarded processes completed;
all 76 frozen cost cases were measured. Only 26 meet all admission gates:20/24
targets and6/52 controls. The failed gates remain unchanged, with no retries,
threshold adjustment, case removal or candidate tuning.

## Source and admission

HEAD595b51b5ac8a5b3bb5dce6708fffa774b350953e,
master6f68e24e8ddac42b948da8fcc2d636c010751194. MA-O copies of driver/auditor/
launcher/guard and env Project/Manifest are byte-identical to MA-N; only command
absolute driver/output paths change. The candidate is frozen MA-L and applies
private MutableArithmetics scratch only through the admitted selective route for
exact eight-term Rational{BigInt} rows. Other row lengths/types use the preserved
generic arithmetic. No new production method, dependency resolution or test edit.

Fresh independent admission:27 checks/25 direct bindings, all3924 launch hashes
and73 complete source trees, all3884 prior records retained. The exact observed
RED expression is required; FileWatching/Sockets sources are prospectively bound.
Unknown runtime module paths fail closed. All loaded module paths passed this
run's check; ordinary loading is not a cache/native-loader closure proof. MA-M's
failed run and missing historical pins remain failed; no retrospective pass.

## Correctness and execution

Original RED produced8Pass/2expectedFail at exactly
`(MAL_TRACE[]).scratch == 1`; candidate GREEN3787/3787 passed across222 fixtures.
Tests include exact decisions, route boundaries, private-leaf ownership, alias
preservation, stored/ambient BigFloat precision, fallback and snapshot sensitivity.
All process output/input snapshots and ambient/trace restoration checks passed.
No weakened arithmetic safeguard, tolerance or raised precision was introduced.

Stage audits passed16/16,14/14,14/14. Each exit0; invocation elapsed17.752368596,
11.774218027,11.750123753s, cumulative41.276710376s. Guard elapsed17.367123294,11.359232618,11.361071947s (see exact process records). These inclusive durations
are resource-cap evidence, not benchmark speedups. Maximum admitted3x120s and
360s total were respected; all three allowances are now consumed.

Same76 cases/3warm+7measured alternating pairs/128 complete helper calls perwindow
in each process:4560windows (1368warm/3192measured),583680timed calls,456 first
calls,888GREEN+4RED helper entries. No added numerical probes. First-call/loading/
qualification costs are separately recorded. All measured compile/recompile are
zero. All35 in-window GC samples, including27 measured, remain included; no
outlier or GC-window filtering. Whole calls include selector and fresh scratch.

## Cost result

Ratios below are candidate/reference, paired whole-call medians; lower is faster.
The complete76 rows and all per-process medians, bytes, events, wins, ranges and
MAD remain in aggregate.json; cost-results.tsv is a readable projection.

| Class | Passed | Pooled time ratio range | Per-process bytes ratio range | Events ratio range |
| --- | ---: | ---: | ---: | ---: |
| Targets |20/24|0.840413–0.953667|0.656696–0.665483|0.694571–0.702939|
| Controls |6/52|0.853187–1.333333|0.578253–1.085830|0.623726–1.131303|

Target byte/event medians decrease in every process. Local pooled target times
are about4.6–16.0% lower, but four targets fail the required18/21 faster-pair count;
one also fails pooled<=0.95 and one processmedian<1. These are overlapping
failures, not six distinct cases. No target gate is relaxed on observed medians.

Control failures overlap:33 cases increase some process's byte median,31 fail
pooled<=1,28 fail some process<=1.02, and one increases events. Small byte differences
also occur in unchanged generic branches; these observations do not establish
additional source-level allocations or their mechanism. Tiny timing differences
and single-case ratios cannot prove universal regressions or improvements. All
original strict gates nonetheless apply and reject this candidate.

A concrete material regression is `tail-zero`: pooled time ratio1.103281;
each process median adds39920 bytes and1664 allocation events per128-call window
(bytes ratio1.085830, events1.131303). The selector has already activated private
scratch before later zero terms. This false-positive route is an explicit source
and measured limitation; it defeats the required non-regression scope. By contrast,
other selected tail controls (unit/fixed/cancel) pass, with ratios0.870575/0.853187/
0.853230. These controls do not justify dropping tail-zero or changing the rule.
`ordinary-free` ratio1.333333 is the largest pooled control ratio on a very small
operation; absolute windows remain in raw data, and no broad33% claim is made.

## Work, allocations and retained memory

No production code was changed, so no new production setup/refactor/iteration/
recovery/certification work or persistent cache was introduced. In this candidate,
selected rows create owned temporary MA scratch; selection checks and arithmetic
stay in the timed helper, with row work scaling with terms and BigInt limb sizes.
Inputs and mutable scalar leaves passed the scoped preservation/ownership checks.
The tail-zero extra work/allocations are unnecessary relative to the existing
fallback for that control, and are a reason to reject this implementation.
No claim of global optimality or proof that every remaining cost is unavoidable.

Diagnostic fixture construction, snapshots, exact oracles, serialization and source
hashing are outside measured windows. Their work is necessary evidence overhead,
not a solver speedup. Reported bytes/events are Julia aggregate allocation counters,
not live/peak memory, a native allocation/free ledger, GC neutrality, or proof that
all retained owners are freed. Three separate short processes and tiny standalone
row fixtures do not establish sparse/dense whole-presolver or end-to-end benefit.
No full presolver, public solver, basis factorization or LP was run.

39 resource samples:minimum available22682096KiB, swap0; terminal available
23166960/23234884/23254284KiB. Fresh all146groups ANDsessions absent/noJulia,
including runner/child9849/9850,9882/9883,9906/9907, with boot/start_ticks/initial
wrappercommands recorded. The process capture is initial command evidence, not
a hidden post-exec loader capture. Protected user files unchanged.

## Evidence and continuation

The preadmitted aggregate ran once and independently revalidated stage schemas
and current raw hashes before computing gates. Separate postexit postcheck.py
ran once:28PASS, all3924 hashes unchanged, all76 aggregate rows independently
recomputed, resource/process closure and input/command links verified. It is a
postexit supplement, not a retroactive launch pin. Source tree/pin checks are
not arbitrary alias/native ownership or transient-memory-peak proofs.

Fresh independent result review is required before diagnostic publication.
Publication must preserve all raw/falsegate records, use separate PASS closure
and an exact complete staged name/blob list before failfast commit/push. MA-N's
ten current STATUS/roadmap bindings map only to MA-O before-copies; older maps
remain unchanged. Current continuation will record the rejection.

This exact selective route is NOT promoted. No automatic repair/retry or new
variant is created here. A different future approach requires a separate concrete
plan; this result does not reject MutableArithmetics generally. Broader performance
plan remains OPEN. Master/production/tests/env/CI unchanged; CI off, HH disabled,
automation paused. All MA-O scripts/raw/admission/checks freeze after publication.
