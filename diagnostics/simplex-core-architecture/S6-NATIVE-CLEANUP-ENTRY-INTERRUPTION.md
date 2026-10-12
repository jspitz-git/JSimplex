# S6-AN: native owned-bound cleanup entry interruptions

Qualification-1 executes exactly two NEW Float64/PFI lifecycles in one guarded
Julia process: stop and throw. Both qualify: 37 + 35 = 72 assertions, exit0,
49 offline audit gates,629 launch pins,628 preserved AL pins,212 binary64 checks
and10 independent verification checks. No production/test/workflow change.
This is new declared entry-boundary coverage, not a fix or reproduction of the
three historical cleanup failures, and not an experiment in real deadline expiry.

## Calls, state, and outcomes

Each case calls the actual source-extracted shifted_primal_workspace helper once
(including its original shift assertion), initial _primal_optimize! once, constructs
one budget, then calls public run_from_basis! once with the default native policy.
The original helper and permanent six-assertion success test remain byte-identical.
No neighboring testset, old driver, success control, adapter, observer, extra basis,
quality/certificate/component solve, private retry, or warmup is evaluated.

The initial optimizer is OPTIMAL in each case, with 2 FTRAN,3 BTRAN,2 pricing
kernels and0 refactor kernels. Selected initial state and complete options/policies
match saved AL. Represented x=s=-9*t has binary64 bits beae32f0ee144531,
basis[2], states[AT_LOWER,BASIC]. The working equation x-s=0 holds exactly.
The original bound remains violated before and after interruption; no primal
certificate is claimed or called merely to inspect the endpoint.

Both public driver windows have zero deltas in every existing kernel counter,
iterations and refactorizations. Each actual callback is entered exactly ONCE,
counted before returning/throwing. Owned journal identity/owner, active bounds,
lower/upper storage identity and aliases, selected point/prices/rho/costs/basis/
states, original model, scaling, options and native policy are preserved. The
journal remains active for bounds (its cost-active flag is false). The shared
start_ns is unchanged, options restored and budget synchronized.

- Stop returns TIME_LIMIT, message `time limit reached during feasibility recovery`,
  with primal/objective/basis absent. Exactly one checkpoint event is added.
- Throw propagates the identical precreated SingularException(29), with no result
  and no added event. The catch is outside the public driver; no numerical failure
  status is substituted for the caller's exception.

Neither case adds a correction, restoration, phase cleanup, certification or
failed-certification event. These facts agree with the existing first guarded
entry before basis verification, normal checkpoint construction, and exceptional
unwinding/finally synchronization. They do not establish every recovery lifecycle.

## Clock and observation limits

The original30second/20iteration options, original tolerances1e-7/1e-7/1e-12,
arithmetic and numerical safeguards are unchanged. No start assignment/reset,
longer/removed limit, sleeping, backend or precision change occurs.

Elapsed from each workspace's OWN start, public driver brackets are:

| Case | Before | After | Interpretation |
| --- | ---: | ---: | --- |
| stop | 0.080177600s | 0.080184700s | expiry excluded within this new bracket |
| throw | 0.000154200s | 0.002429600s | expiry excluded within this new bracket |

Callback count1 is the direct observation of the declared interruption route.
Brackets assume monotonic time and do not capture a private clock check. These
are separate natural clocks, not matched timing pairs. Different harness/function
compilation placement and prior specialization within this process prevent timing
comparisons with AL or speedup claims. No explicit warmup was added.

Existing kernel timing is enabled only after real helper setup. Disabled setup
zero counters are not zero setup work. Four tiny owned captures per case and
assertion/bookkeeping work consume the shared budget; instrumentation neutrality
is not claimed. Serialization/rationalization occur after both windows. The
callback itself owns only a bounded Ref counter and the precreated exception;
there are no callback numerical operations or growing callback ledgers.
Zero driver kernels is not zero total computational work: existing original-cost/bound checks can scan vectors before the first
guard; policy/options/budget bookkeeping, checkpoint/result construction and
the caller's observations also remain.

## Audit, preservation, and continuation

Fresh host checks show prior425975/425976/425967 absent before launch and new
runner430176(start24894004),child430177(start24894085),launchgroup430144 absent
after completion, same boot20de7dde-704e-41c8-bee7-b8511c0a86b0. 22 resource samples
remain within the RAM/swap guard (see independent-verification.json for exact
minimum). Guard exit0/pins_unchanged is supplemented with independent actual
file/resolved-path hashing, actual helper hashes, full source/test/CI equality to
master354bb1f, raw/portable equality, six user hashes, and source-bound assertions.

Evidence: results/S6-AN/qualification-1-{report.toml,process.json,pins.json,run.log,
audit.json,driver.jl,resources.jsonl}, preflight.json, host-before/after.json and
independent-verification.json. The new exclusive auditor and numerical driver
must NOT be rerun on accepted evidence. No previous accepted driver was run.

Fresh independent gpt-6-astra review accepts with no Critical/Important/Minor
findings and no unnecessary new production work/memory. See the review report.
After acceptance, separate S6-AO permanent coverage plan was written; it remains
unimplemented and does not repair the old timeout hypothesis.
S2-A/S6-J/wholeAF rejections, historical three failures, actualx64/fullsuite/broader
S6 gaps remain. CI stays disabled. Existing production work/memory is unchanged;
no benchmark is warranted for these bounded diagnostics alone.
