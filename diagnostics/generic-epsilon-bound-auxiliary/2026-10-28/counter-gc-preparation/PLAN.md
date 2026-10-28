# One fixed post-warm full-GC preparation control

Hypothesis: prior preparation/garbage/allocator state can affect native aggregate byte traffic. No measured GC cause or original malloc cause has been proved. Source evidence: counter-capture-diagnosis.json. This is exactly one preregistered experiment, not repeated sampling until a pass.

The same three ordinary whole files/23663checks, fixtures/data, three warm pairs, three measured alternating pairs, strict event/byte and3percent thresholds stay unchanged. Only four named Rational gates get ONE fullGC after existing warmups (and existing zero-allocation wrapper qualification for DUAL), before all measured windows. No GC between arms/pairs, no filtering, no retry, no changes in production source/test/env/CI. Preparation GC seconds/bytes/events/compile/GCraw cost are separately recorded after measurements. Full original source recovered exactly by removing logging/preparation insertions.

Single900s/892guard process, usual fresh fullgroups/sessions/boot/start/command/noJulia/refs/pins/resource controls and independent admission/result review. A pass demonstrates sensitivity/control observations only; it does not prove original cause, approve permanent test changes, waive failedMASTER or qualify release. If controls still fail, no adaptive GC, batch growth, threshold change or further tuning follows from this plan.
