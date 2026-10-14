from control import *
P=D.with_name('PRESOLVE-EXACT-CACHE');B=R/'diagnostics/simplex-core-architecture';h=host(rd(D/'posthost.json')['groups']);entry=rd(P/'host.json')
req(not h['matches'] and h['head']==entry['refs']['head'] and h['master']==entry['refs']['master'],'fresh host');save(D/'continuation-host.json',h)
status=B/'STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
for p,n in ((status,'STATUS.md.before-cache'),(road,'roadmap.md.before-cache')):req(p.read_bytes()==(P/n).read_bytes(),'unmodified continuation beforecopy')
text='''The Float64 exact-conversion cache experiment is complete as a diagnostic.
See PRESOLVE-EXACT-CONVERSION-CACHE.md and results/PRESOLVE-EXACT-CACHE-PIPELINE.
The user changed the success criterion to faster whole presolve without increased
allocations; whole-solver acceleration is not required. Original component/public
sequence stopped at process1 (46.803587974s,exit1,58/59checks): candidate sc50a rep8
recorded6.682501mscompile and89.252609msGC; output/input checks true. Original
false gate/raw unchanged, stages2–4 absent, no retry of that sequence.

New separately admitted whole-presolve study used the SAME candidate and overlays:
four R/C/C/R processes,47.204951727s total;352presolve calls,48driver checks,
four17-gate audits,224measuredwindows compile/recompile/GC0, exact full-result
signatures/inputowners preserved.32separately timed warmupGCs, not continuous-GC
throughput. Afiro10.8–16.8%,adlittle7.4–11.6%,chain13028.0–30.3% lower median time
in bothblocks with lowerbytes/events; sc50atime inconclusive. Unconditional cache
NOT ACCEPTED: unique sparse/densecontrols add~2.1%/~1.6%bytes and13/18events;
sparse-repeated block2 anddense-unique block1 also failtimeguard. No excuse as
allocatornoise. Candidate addsonehash/reachedcoefficient andO(u<=10000)temporary
cache; no production/test/env/CI/master changes, no automatic integration/tuning.
Combined numerical process elapsed94.008539701s, not a benchmark metric.

This exact candidate is stopped here. A selective variant needs its own concrete
eligibility/work design and review; none is prepared or admitted by this result.
Do not rerun frozen experiments or reopen MA-Y/HH/DSE/controller/isolation/cleanup
routes. Broader plan OPEN, CIoff,HHdisabled,automationpaused,master6f68e24unchanged.
Fresh186groups ORsessions/noJulia/refs before continuation; source514/protected6
and all launch pins unchanged. MA-Y-FALLBACK current closure/publication/continuation
STATUS/roadmap hashes map ONLY to PRESOLVE-EXACT-CACHE beforecopies (sixbindings);
all older mappings stay. All new and old raw/scripts/pins/reviews FROZEN NEVER
RERUN/rewrite. Fresh host and preserve exact continuation bytes before future work.
'''
s=status.read_text();needle='## Exact next action\n\n';req(s.count(needle)==1,'statusanchor')
s=s.replace(needle,needle+text+'\n## Previous MA-Y-FALLBACK analysis (completed)\n\n',1);status.write_text(s)
with road.open('a') as f:f.write('\n## Presolve exact-conversion cache — diagnostic decision 2026-10-14\n\n'+text)
save(D/'continuation.json',dict(all_passed=True,qualification_accepted=False,sha256={str(p):sha(p) for p in (status,road,D/'continuation.py',D/'continuation-host.json',P/'continuation-map.json')},scope='Original failed attempt preserved; user-updated presolve experiment correctness passes but unconditional allocation/performance screen rejected; no new variant admitted.'))
print('Continuation updated with fresh',len(h['groups']),'groups/sessions clear; six exact mappings preserved.')
