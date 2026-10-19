# Independent P011 typed-repair review

Disposition: ACCEPTED — PREPARATION ONLY. No actionable findings. This is a bounded source-only review, not Julia syntax acceptance, a runtime pass, launch admission, or production approval.

Reviewed diagnostic HEAD `f179c815dfdd0db969b485a0685fe4d247225fb0` and master `26e2291745999f485a74f643298ca997d65c7205`; independently read both refs. No Julia, Julia parser, macro expansion, import, compilation, IR query, numerical work, old script, driver, or auditor was executed. Review used source reads and new inline Python standard-library byte/hash/text checks. Only these two new independent-review files were written by the reviewer. No commit or push.

## Boundary and evidence

Independent forward reconstruction and inverse restoration both match byte-for-byte. Removing exactly the helper insertion and reversing exactly the three-line P011 block replacement recovers frozen panel-tests.jl SHA256 `694c34056e4a1fda5819d494022cb154694ef3412e7176571949c28e00af3f41`. The old 94 literal P IDs remain once each in their original order, and P095–P102 are the only eight new IDs. P012 and every other original source byte outside the two stated edits are preserved. All nine input hashes and all eleven producer source-check bindings were independently recomputed and matched; the producer scripts were not rerun.

The accepted shared-zero candidate is exactly SHA256 `19dccf0d5259d730b19333b2b1c685a50ee76f93d2cc3b242cb54a762cae9295`. Its n32,row1 path constructs the literal expected dimensions rejection and returns before scanning packed entries. This review does not substitute the original zero factory. The saved run report supports concrete eligibility 0 bytes/0 events, its consumed-result companion 0/0, and reduced original-shaped 208 bytes/1 event. These are prior evidence, not measurements of this new full module.

The installed timing.jl source (SHA256 `41f586b1daee16cac7ae23543e02727fc85b6a427a13900ddd6eb18a9449f613`) shows the explicit function/argument meters surround an @noinline call, discard its result, and report bytes or GC allocation count. Its macro builder wraps a non-simple qualified callee expression in a zero-argument closure. The report appropriately describes boxing/materialization as plausible; neither source nor a matching byte size identifies the historical allocated object. No causal certainty is inferred.

## Helper and assertion review

The typed Carrier argument provides an explicit boundary independent of the reassigned testset-local binding. The return annotation names the actual BGPanelDecision. The consumed helper writes that full decision to a pre-existing RefValue and returns nothing. The direct and consumed calls each retain independent zero-byte and zero-event assertions; no allowance, subtraction or threshold relaxation is introduced. Fixture/Ref creation, before/after snapshots, comparisons and Test recording occur outside the four source-visible measured calls. Five warm calls include each measured helper/meter combination.

Each measured consumed call resets the sink to an invalid sentinel, then saves its result before the next reset. The sentinel fails the literal decision predicate, so an omitted store cannot pass by reusing a warmed result. P098–P100 compare start, count, accepted, reason, finite and all twenty counters, independently of the candidate decision factory. The direct discarded-result measurements are complemented by these observable-result arms; they are not asserted to have identical runtime/compiler behavior.

P101/P102 bracket both warming and measured calls. Values cover packed IDs/values, incidence, shared row permutation and inverse, column permutation and inverse, row_columns_ready and every row-cache field. sparse is concretely Nothing; prepared is explicitly required to remain nothing. Selected identity checks cover the Carrier, upper container, column vectors, incidence container/elements, cache, shared order and its buffers, every packed ID/value buffer and order, and every array-valued cache field. PackedUpperColumn, UpperRowIndices and UpperRowOrder are immutable wrappers; their mutable buffers are represented. The fixture starts with a shared order, and checking every column's order identity makes the single shared-order value snapshot sufficient for this fixture. This is not a general graph audit or transient-mutation detector.

The actual master-stage cache declaration/constructor and index definitions were checked against the diagnostic source: exact cache-region and complete indices equality hold, with independent stage hash verification. The whole factorization file differs only in native-pivot constructors, as the supplement reports; no whole-file equality is assumed. Actual-stage factorization SHA256 is `685d4356d83a4f62f2cf17f08a70f5987ba78d18499dc8ee6975405ae4a939f2`; actual-stage indices SHA256 is `96659cddfae345701aed6c320a86fbeef4c6c4c95819864e363fcca04de3e61d`.

## Computational work and memory

No unnecessary material work or retained-memory cost was found in the scoped change. There is no production-code change, no new production scan/solve/copy/conversion, no precision or tolerance change, and no changed numerical safeguard or growing cache. All additions run in the cold n32 test probe. Independently counted source entries: five warm plus four measured plus unchanged P012 = ten, versus the previous warm/measurement/P012 = three. The increase is seven cheap-rejection entries, not seven observed optimized calls.

Each of the two snapshots copies 32 ID vectors, 32 value vectors, 32 incidence vectors, four permutation vectors and four array-valued cache fields: 104 leaf arrays plus three nested snapshot containers. The owner list has 9 initial entries + 32 incidence entries + 3*32 packed entries + 4 cache-array entries = 141 references (including repeated shared references, not 141 distinct objects). Work scales with n plus stored packed/incidence/cache entries; no update chain or basis solves are involved. Snapshot/owner graphs are local to the probe; only decisions, scalar measurements and booleans are returned. Deepcopy bookkeeping, compiler/Test storage and actual heap event/byte totals are additional and unmeasured. The added snapshot passes and separate measurement arms serve the requested state/result checks and are justified in cold diagnostics. Fixed module helpers remain loaded; no whole-process memory-release claim is made.

No before/after timing benchmark was required or performed for this cold test-only edit. Sparse/dense hot-path and all-precision performance coverage remain absent, as appropriate to the bounded Float64 n32 probe. Zero inner-window targets do not imply allocation-free setup/tests or an end-to-end speedup.

## Declined runtime judgments and next preparation

This review declines to certify Julia parsing/lowering, method availability/dispatch in the eventual parent, compilation/specialization, measured bytes/events, optimized execution counts, sentinel-test runtime outcomes, input-preservation outcomes, numerical correctness, or full-module assertion totals at runtime. It does not identify the 208-byte object. It does not reopen historical RED2 or treat the six unreached N026 checks as passed.

A separately prepared and independently admitted RED/GREEN driver/auditor must bind this exact test file, accepted shared-zero panel, ordinary master stage, HarnessRecords and all actual dependencies; include exactly one version of BGBlockedPanelTests in a fresh parent; account for P095–P102 as well as every old ID and dynamic count; define the exact RED comparator and expected failures; preserve original-shaped control evidence; separate preparation from inner windows; and obtain fresh host/runtime/source checks before any launch. The old file/count/pin admission and six-failure expectation are not reusable. No launch is authorized by this review.

## Exact reviewed candidate bindings

- panel-tests.jl: `15faee72f0f40bddae911818379c99d56aeb4a96e24cb7ce901691f188888910`
- helpers.jl: `24164ea279f5eeaaf5a9860ffb11a813ac98e1d8ed8d950c957cd4d2be6c5f6f`
- original-block.txt: `d0db6d92444149eab36cda6dfed7aebc716d016407611739501882dcd5c39cde`
- replacement.txt: `4778187253863acef669f2f95f55adabeeb082360681b41808eda6ca9442c89e`
- REPORT.md: `7dad36e730072c56c73765c609507aed08bfcb439647cffac621e34121643a67`
- inputs.json: `2894e68b802a2b3eb4bf88791ab0aad89c3db9b5cf83f6281e1539e4b1b29559`
- source-check.json: `2143b5b059b49087437c548d448d6c827e88a32809d840c448e184d5083e80ae`
- stage-supplement.json: `07c78cd2c5bc9198279cf88c3e05d448974970ac87c2c95828567eadcb2894e3`

The accompanying JSON contains every reviewed directory-file binding plus all pinned source-input and actual-stage bindings. Binding a historical artifact is not a fresh full audit of its execution.
