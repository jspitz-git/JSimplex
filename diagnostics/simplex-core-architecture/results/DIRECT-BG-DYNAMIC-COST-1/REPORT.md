# Dynamic BG shared-slot U — first comparative cost result

The candidate is STOPPED under the accepted fixed Task3 performance gates. One authorized cost1-300 process completed all8cells/160windows with Juliaexit0. Full lifecycle paired median times were lower in every cell, but allocated bytes increased in6/8cells and reachable factor graphs exceeded+10% in all4dense cells. Only sparse96/native passed all first-process gates. No second process, ordinary comparison, tuning, production integration or retry was performed or admitted. This does not establish that other dynamic designs cannot improve performance.

## Execution and diagnostic discrepancy

Fresh independent admission accepted32checks,1859sealed files/83stage files,1860exactreview bindings,232historicalgroups ANDsessions/noJulia. The actual launch bound1862files. One runner363754(start_ticks22268778) and child363755(start_ticks22268832), each own PGID/SID, boot284d2228-1d9a-4c5f-913c-b9f1098b5838. Inclusive supervisor time13.06566240399843seconds, below outer300/inner292. This includes loading/compilation/setup and is not a benchmark timing. Twelve resource samples, minimum availableRAM22160068KiB,swap0,terminalRAM22812728KiB,childmaxRSS801764KiB. Fresh full234groups ANDsessions clear, noJulia. No runtime warnings appeared.

The canonical one-shot auditor returned all_passed=false,pure_timeout=false with RuntimeError('Raw schema/count/path'); launcherexit1 is preserved. Juliaexit0 alone was not accepted. The frozen expected loaded-path list inherited Test, whereas the sealed cost driver intentionally records exactly JSimplex,LinearAlgebra,SparseArrays,TOML,PrecompileTools. All five reported paths and all other final schema fields match exactly. The missing diagnostic Test key is the only mismatch; it does not prove Test was absent from the process. The original audit, raw data, driver, expected paths and controls remain unchanged, and the auditor was not rerun.

New supplement.py checks this narrow mismatch, original failure bindings, full seal/launch integrity, schedule and descriptive costs:31PASS. Independent new saved-data review validates199checks including all4416exact residuals(3840timed+576probe),80bitwise pairs,8control/probe cases, unchanged inputs and measuredcompile/recompilezero. No tolerance, numerical output or raw file was changed. Result acceptance is diagnostic and supplemental; it does not retroactively turn the original audit into PASS or unlock the canonical second-process launcher. The pre-output postcheck.py draft remains UNEXECUTED because its original-PASS premise was false. The reviewer's initial login-shell PATH mismatch is separately preserved; actual non-login launch environment matched without rewriting environment values.

## Whole lifecycle results

Paired ratios are dynamic/packed medians of7measured pairs, not ratios of side medians. Lower is faster. Bytes are aggregate GC allocation traffic; events are allocation events. Graph is reachable Julia factor memory after the final refactor. Each cell also has3warm pairs. Native uses threshold_one; Markowitz uses default. Both normalize identically.

| Fixture | Backend | Paired time ratio | Faster | Bytes reference → candidate | Events reference → candidate | Final graph bytes reference → candidate | Failed gates |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| sparse32 | native | 0.9721 | 4/7 | 294,472 → 301,448 | 1,274 → 663 | 11,568 → 12,024 | time_median, allocation |
| sparse32 | markowitz | 0.8704 | 7/7 | 273,376 → 278,576 | 3,848 → 3,231 | 11,488 → 11,744 | allocation |
| dense32 | native | 0.9507 | 4/7 | 755,584 → 860,408 | 1,282 → 723 | 25,696 → 43,672 | time_median, allocation, memory, probe_memory |
| dense32 | markowitz | 0.9220 | 4/7 | 349,712 → 454,520 | 1,132 → 573 | 25,696 → 43,672 | allocation, memory, probe_memory |
| sparse96 | native | 0.9215 | 7/7 | 663,592 → 648,960 | 2,513 → 687 | 32,208 → 32,456 | none |
| sparse96 | markowitz | 0.9566 | 5/7 | 770,216 → 743,984 | 10,571 → 8,690 | 31,808 → 31,056 | time_median |
| dense96 | native | 0.7881 | 5/7 | 4,682,392 → 5,719,976 | 2,785 → 744 | 173,152 → 349,080 | allocation, memory, probe_memory |
| dense96 | markowitz | 0.7905 | 5/7 | 2,598,264 → 3,638,696 | 2,635 → 597 | 173,152 → 349,080 | allocation, memory, probe_memory |

The final and untimed checkpoint graph gates fail on both dense sizes: maximum corresponding ratios1.6995641345(dense32) and2.0160321567(dense96). Allocation events fall everywhere, but bytes are the controlling separate gate and rise in six cells. Sparse32 bytes rise1.90–2.37%; dense32 rises13.87–29.97%; dense96 rises22.16–40.04%. Sparse96 bytes fall2.20–3.41%. The first-process all-eight-cell prerequisite is false. No backend qualifies across all four fixtures, and a second process cannot repair a per-process failed gate.

These are short component lifecycles, one process, and no reversed-order confirmation. Five measured windows had nonzeroGC; they are retained. Dense96 paired ranges are0.2696–2.8582(native) and0.2036–3.3430(Markowitz), MAD0.07051/0.12345. Small-window/order/GC variability limits speedup inference. Raw distributions and all nested statistics remain in supplement.json and original window files. There is no end-to-end solver, ordinaryBG, native-peak or universal speedup claim.

## Work and memory interpretation

Whole windows include construction/export/normalization/arena creation,16FTRAN+8BTRAN,8updates and2fullrefactors. Symmetric six-element nested clocks are included; nested times are subsets and must not be added to whole timing. Input scans, preliminary residual checks, exact-token serialization, graph inspection and separately named instrumentation are outside windows. Timed dispatch contains no probe counters or full slot-invariant scans, and old factor owners are not accumulated.

Nested update medians fall substantially: dense96 native758.9→173.4microseconds and Markowitz751.8→178.7. But FTRAN medians rise72.8→152.4/74.3→155.5microseconds and BTRAN56.7→95.3/54.7→96.2; construction/refactors generally rise too. These are descriptive subsets, not isolated causal measurements. They are consistent with trading cheaper row/column updates for linked-storage traversal and larger owned storage. Source algebra is56*C+64*n arena payload. Dense96 probe capacity reaches6984 with4656live slots; two observed probe growth attempts copy65184scalar entries total and reach651840bytes of old+new arena payload. These counters describe the separate successful probe only, not all timed or native operations. Each array/header/backend cost remains additional.

Per-process source API ledger: timed160constructors/320refactors/1280updates/2560FTRAN/1280BTRAN; controls16constructors/32refactors; probes24constructors/48refactors/192updates/384FTRAN/192BTRAN. Total200constructors/400refactors/1472updates/2944FTRAN/1472BTRAN/zero copies;600backend/export entries and<=300native orientation solves are source-derived bounds, not complete observed PREforward/native work. Probe11checkpoints/cell preserve structure/order/history/bitwise outputs. Copy and refactor transient coexistence are source contracts, not measured peaks. Aggregate GC counters may include native allocation traffic; summarysize and processRSS do not isolate native live/peak memory.

No unnecessary NEW production work/memory was introduced: production/src/test/env/CI/master remained byte-identical. The measured diagnostic candidate has material excess storage/allocation costs and is not promoted. There is no scope to silently shrink indices, add mirrors/dense fallback or change fixtures in this admission. Any follow-up requires a new design. Preserve all frozen evidence, initial rejected review and this false audit. Master26e2291745999f485a74f643298ca997d65c7205 unchanged; CIoff/HHdisabled/automationpaused; broader plan remains open.

## Continuation bindings

Current cost-preparation closure/publication STATUS/roadmap hashes and blobs map only to this record's exact before-COST1 copies. All older mappings remain. Independent result and final closure review precede separate PASS diagnostic closure and exact staged/committed publication. PASS closure means the result and its rejection are faithfully preserved, not that the candidate or original audit passed.
