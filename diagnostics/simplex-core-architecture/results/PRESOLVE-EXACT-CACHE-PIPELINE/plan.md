# Whole-presolve experiment under the user's revised criterion

The user now says whole-solve acceleration is unnecessary: faster presolve without
increased allocations suffices. This independently admitted new experiment measures
presolve_problem, not a rerun of the previous dependent-pass/public-solve sequence.
Original PRESOLVE-EXACT-CACHE stopped after its first process (46.803587974 seconds,
exit1, 58/59 reached checks true). Its sc50a candidate window8 had compile6.682501ms
and GC89.252609ms; all observed output/input checks true. Those aggregate counters
do not identify a particular compiling method or prove GC caused compilation.
No original gate is waived or raw/script rewritten; original stages2–4 never run.

Candidate and ordinary overlays are byte-identical to the independently admitted
three-edit Float64 cache. Generic source and all safeguards unchanged. Ownership,
O(u<=10000) extra temporary cache roots and per-reached-coefficient hash lookup
remain exactly as described in the original plan/admission. No production edit.
Original sixteen boundary/generic cases and two nonfinite behavior comparisons
passed and are reused, not repeated. No whole public solve in this new experiment.

Four serial processes R,C,C,R, <=64seconds guard setup+execution, <=70 with cleanup,
<=280 cumulative. Combined with original process <327 seconds if all caps respected.
All original memory/thread/VM/heap/no-auto-precompile settings retained. No retry.
Fresh178groups OR sessions/noJulia/boot/refs; unchanged old and candidate hashes.
Copied guard exact; supervisor only tightens84/88/90 to64/68/70 seconds.

Eight unchanged model inputs: afiro,adlittle,sc50a,primal-chain130 and sparse24 /
dense16 repeated/unique coefficients exactly copied from the original driver.
Each process/case: 1 cold +3 warm +7 measured whole presolve calls =88/process,
352 total. No standalone solver, basis, certificate or instrumented callbacks.
Model parsing/setup outside timing. Cache construction and all nine presolve passes
inside. One explicit GC after warm calls per case, separately timed:32 total.
This warms GC/finalizer paths; it neither proves a cause for the original compile
sample nor measures uninterrupted long-run GC throughput. No GC sample removed.
Measured compile/recompile must still be zero, all result tokens (whole reduced
model/postsolve maps) and original input owners/values must match.12driver checks,
8files x10windows plus cold/GC metrics each process, exact signatures across all4.

Before-run screening criterion: both ABBA block comparisons C2/R1,C3/R4 show >=5%
median presolve improvement on >=2 of four real LPs. Across ALL8cases in BOTH blocks,
median bytes AND allocation events must not increase, no time regression>5%.
Report every ratio, dispersion/range, cold/GC work, incomplete coverage. Equality
is literal for allocation medians; do not excuse failed gates as allocator noise.
No whole-solve benefit required. These are exploratory screen gates, not proof of
universal speedup, statistical significance, full native free/retention or CI.
Failure closes this unchanged candidate here; no tuning. Independent concrete
admission before launch; independent result review, preserved raw and exact
publication afterward. Broader plan open, CIoff/HHdisabled/automationpaused.
