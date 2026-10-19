# Initial allocation-provenance admission rejected

One material finding prevents admitting this sealed profile300 package.

**Private diagnostic helper conflicts with Base.summary.** driver.jl defines unqualified summary(t,outputs) and calls it twice. The pinned Base exports summary (base/exports.jl:704), and the installed module manual requires explicit import or qualification to extend imported functions. This diagnostic intends a private result serializer, not an extension of Base.summary. Rename the helper and its two call sites to a unique private name in a separately preserved correction. Do not overwrite the original driver, preparation or seal.

The collision was identified by source inspection; Julia was not parsed or executed. The original package has no reservation, invocation or numerical output. All 2348 preparation pins and 2351 sealed-file hashes/resolutions match.

No other material blocker was found in the complete driver/helper, Profile.Allocs API, source/runtime/policy bindings, saved-output auditor, exception cleanup and guarded launcher review. The accepted lifecycle slice is unchanged. The fixed schedule is 80 constructors,160 refactors,640 updates,1280 FTRAN,640 BTRAN, with up to120 additional native orientation calls, and768 observed vectors. Profile start/stop/fetch/clear and Alloc.type/size/stacktrace match the pinned stdlib source. Full symbolic C/runtime/harness frames are retained and aggregated only after profiling stops.

The 200000-record test occurs after fetch has decoded the profile; it is not a capture-time or decoder-memory bound. The 8 GiB virtual-memory cap, minimum available RAM and bounded process deadline remain the hard guards. Decoded records, aggregation, output rows and the prior side can coexist; this diagnostic cannot claim constant memory or a universal peak. Julia heap provenance is explicitly narrower than all native allocation/GC-counter work.

The work/memory review found no new production work or retention: production and the candidate are unchanged. Profiling and stack decoding add intentional diagnostic work only. No profiled time or performance-qualification inference is allowed, and the earlier fixed-design performance rejection remains in force.

A fresh separately frozen correction and exact-stage admission are required before the first numerical attempt.
