# Direct BG export workspace: exact allocation provenance

This is a new allocation-site diagnostic of the frozen candidate, not a new performance qualification. The original cost rejection remains unchanged. No production, candidate, test, environment, CI, master, or continuation file was changed. No optimization is implemented here.

## Evidence and scope

`runs/profile300` contains one independently admitted, guarded process, exit 0, inclusive elapsed 98.41257106799458 s, peak child RSS 978148 KiB. Its admitted one-shot audit passed. All 256 historical/new process groups and sessions are closed; terminal available RAM was 22999828 KiB, swap zero. The 300 s outer / 292 s inner limits and original memory guards were retained.

Four frozen sparse/dense32/96 fixtures, two backends and two sides produced 16 full-rate allocation profiles. Each side ran three warm lifecycles, one ordinary observed lifecycle and one profiled lifecycle: 80 constructors, 160 refactors, 640 updates, 1280 direct FTRAN and 640 direct BTRAN entries in total. Native extraction can additionally perform up to 120 orientation solves; these are source bounds, not a full backend attempt count. All 768 stored ordinary/profiled vectors passed the admitted exact residual analysis, paired bitwise output/mode equality and unchanged-input checks. Observed compile/recompile times were zero. The profiled times are not used as performance evidence.

`helpers.jl` is an exact frozen cost-driver slice. The driver profiles the uninstrumented 79-file GREEN stage, not the previous cost probe clones. `Profile.Allocs` and its installed source/dependency paths were prospectively pinned for this run, not retroactively attached to the original cost measurement. The original profiler preparation was rejected before any Julia attempt because a helper collided with exported `Base.summary`; its original seal and rejected review remain in the sibling `...ALLOCATION-PROVENANCE` directory. The accepted sibling changes exactly three occurrences to `bg_alloc_summary`.

`attribution.py` is a new, post-run offline analysis, saved before execution. Its `attribution.json` partitions every stored allocation by full stack, type and size and binds all 16 raw profiles. Neither a previous numerical driver nor an old auditor was rerun.

## Exact added allocation sites

Line numbers below refer to the actual sealed stage source. Candidate `export.jl`, `factor.jl`, `import.jl` and `workspace.jl` in `diagnostics/direct-bg-export-workspace/reproduce` are the corresponding byte-identical sources. Counts refer to one lifecycle: one constructor and two refactors.

| Source site | Observed object and profiler size | Count per lifecycle | Frequency |
| --- | --- | ---: | --- |
| `_bgx_export.jl:84`, call to `_bgx_scale_mode` | `SparseMatrixCSC{Float64,Int64}`, 48 B | 6, native only | Two factor matrix value boxes at each of three exports |
| `_bgx_factor.jl:63`, call to `_bgx_build` | CSC value, 48 B; `_NativePivotPolicy`, 16 B | 2 + 2, both backends | One of each at each refactor |
| `_bgx_import.jl:56`, `return upper,D` | result tuple, 16 B | 3, both backends | Every import |
| `_bgx_factor.jl:10` / `:4` | `_BGXBuildOwner`, 16 B / `BGExportFactor`, 32 B | 1 + 1 | Constructor only |
| `_bgx_export.jl:8`, scratch eligibility call | `Int64`, 8 B, stack includes `ijl_box_int64` | 6 in dense cases, both backends | Integer arguments at each export |
| `_bgx_export.jl:84`, orientation call | `Int64`, 8 B, `ijl_box_int64` | Another 6 in dense native cases | Integer arguments at each export |
| `_bgx_workspace.jl:3` | `BGExportWorkspace`, 48 B | 1 when retained | First eligible export |

The CSC objects above are small matrix value wrappers at call boundaries, not additional copies of the CSC coefficient/index arrays. Their stack sites and 48 B object sizes establish the allocation location; they do not by themselves prove the compiler inference decision responsible. The integer-call source passes `n, nnz(L), nnz(U)`; profiles identify the boxing call and type, not each boxed integer's value. Do not claim a measured integer-cache threshold or an inspected typed IR.

Native orientation `matches` closures are **three on each side**, with equal 32 B sizes. There are **no `Core.Box` records**. Thus a captured-variable `Core.Box` is not the explanation of the additional events in this diagnostic. This does not claim closures are allocation-free.

## Complete event-difference reconciliation

Full-rate profiles include 14 reference-only objects outside the `lifecycle` stack, created while assembling the outer `@timed` result. They are outside its own GC-counter interval and must be excluded when comparing the profile with that interval. Two additional reference-only return tuples at `helpers.jl:45` are inside the interval; they are harness result-materialization effects, explicitly retained in the ledger below.

After separating those outer 14 records, every paired heap-record delta exactly matches the profiled GC-event delta. The native GC counter still exceeds the lifecycle heap-record count by 171 / 183 / 171 / 180 events for sparse32 / dense32 / sparse96 / dense96 respectively, equally on both sides. Markowitz residuals are zero. This is count reconciliation, not a complete native malloc/calloc/realloc ledger or a proof that every native allocation matches individually.

| Fixture/backend | Original accepted cost event delta | New profiled GC delta | New lifecycle heap delta |
| --- | ---: | ---: | ---: |
| sparse32/native | +5 | +5 | +5 |
| dense32/native | +9 | +9 | +9 |
| sparse96/native | +1 | +1 | +1 |
| dense96/native | -6 | -6 | -6 |
| sparse32/Markowitz | -1 | -1 | -1 |
| dense32/Markowitz | -3 | -3 | -3 |
| sparse96/Markowitz | -1 | -1 | -1 |
| dense96/Markowitz | -3 | -3 | -3 |

For sparse32/native, the complete net ledger is:

- +6 native orientation-call CSC boxes;
- +4 refactor-call CSC/policy boxes;
- +3 import result tuples;
- +2 constructor owner/factor wrapper;
- -3 old normalization temporary `Memory{Float64}` allocations at `direct-factor.jl:84`;
- -3 reference `Core.SimpleVector` metadata allocations at `direct-factor.jl:144`;
- -2 reference `DirectLowerBackend` boxes at `direct-factor.jl:172`;
- -2 harness lifecycle return tuples.

This sums to **+5**. All other grouped allocation counts cancel. In particular, neither permutation-mask storage nor orientation-vector allocation counts are reduced for sparse32. Candidate-side overhead excluding the favorable harness return-tuple difference is +7 events in this case; the original whole-lifecycle gate nevertheless correctly observed +5.

For dense32/native the differences from that +5 are +12 integer boxes, +1 workspace, -6 mask allocations (two masks, each BitVector/vector/Memory), and -3 additional normalization data-buffer records: net **+9**. For sparse96/native they are +1 workspace, -3 mask allocations and -2 additional normalization buffers: net **+1**. Dense96/native additionally retains one orientation tuple and avoids eight orientation vectors plus eight Memory objects; its net is **-6**. The saved JSON contains the complete corresponding Markowitz ledger as well, with a zero difference in the residual `other_lifecycle_allocations` category in all eight pairs.

The new dense96/native *ordinary* reference observation has 2826 GC events versus 2785 in its profiled observation and in the accepted old cost median. This +41 anomaly is preserved and its cause is not established by these records. The candidate has 2779 in both new observations. Do not silently substitute these counts or interpret their difference as a new improvement. The other ordinary/profiled event counts agree. Native byte totals also vary between observations; small-object profiler sizes are not GC allocator-rounded byte traffic.

## What this changes in the diagnosis

The exact additional events are concentrated at export/import and refactor call boundaries. The retained workspace itself contributes only one owner allocation where enabled, and sparse32 has no retained workspace at all. Removing workspace retention alone therefore cannot explain or fix the observed sparse32 increase. Repeated allocation of the two vectors per packed U column remains on both sides; the profile does not identify that shared work as the source of the *extra* candidate events.

The concrete target for subsequent design, if requested, is the small-object materialization at `_bgx_export:84`, `_bgx_factor:63` and `_bgx_import:56`, including the dense integer boxing. A concrete dispatch/inference repair must be separately designed and checked; this diagnostic neither proves a particular annotation/inlining change will remove these allocations nor establishes its timing benefit. The existing mathematical checks, ownership/publication order, fallbacks and arithmetic must remain unchanged.

Computational-work/memory review: no production change or new production scans, solves, copies or retained buffers were introduced. The profiling process intentionally retained full allocation stacks and serialized them after each interval. Its 200000-record check happens **after** profiler fetch/decode and is not a capture-time memory bound; the process memory guards provide the actual admission bound. The candidate does show potentially avoidable boxing/materialization at the sites above, alongside required output/storage allocations and measured reuse savings. This is narrower and better supported than attributing the regression generally to the workspace or proposing another storage layout.
