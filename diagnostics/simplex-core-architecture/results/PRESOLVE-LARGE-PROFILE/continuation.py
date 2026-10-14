from control import *
P=D.with_name('PRESOLVE-EXACT-CACHE-PIPELINE');status=R/'diagnostics/simplex-core-architecture/STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
mapping={}
for source in ('closure.json','publication.json','continuation.json'):
 rec=rd(P/source)
 for p,before in ((status,D/'STATUS.md.before-profile'),(road,D/'roadmap.md.before-profile')):
  req(sha(p)==sha(before)==rec['sha256'][str(p)],'continuation bytes changed')
  mapping[str(P/source)+':'+str(p)]=dict(preserved=str(before),sha256=sha(before))
summary='''Large-model presolver attribution completed as a bounded diagnostic; see
PRESOLVE-LARGE-PASS-PROFILE.md and results/PRESOLVE-LARGE-PROFILE. Three inputs,
three processes,243.3857s inclusive total; no candidate/fullsolve. First complete
dispatch sequences runtime1.5623s/medium11.7925s/test42.3303s, all231recordedpass
compile/recompile0. Sparse equality aggregation+propagation dominate ~67–81%.
Traffic1.718/8.171/21.432GB is cumulative allocation, not peak/live RAM.
Runtime3profiles+publiccontrol outputs/inputowners equal. Medium1verifiedprofile,
second27dispatch trace recorded but timeout114.5163s in diagnostic digest: exit-15,
no raw/publiccontrol/repeatvalidation, preserved PARTIAL not PASS. Test1fullprofile,
second22dispatch prefix cooperative stop, finalinput/ambientPASS, no publiccontrol.
Type-name formatting in diagnostic result hashing is avoidable overhead; do not
reuse that implementation for larger benchmarks. No rerun/longer allowance used.

User reminded propagation was already tried. Initial recommendation withdrawn;
prior rounds38/77/137 and MA-P explicitly reconciled. Concrete NEXT PROPOSAL ONLY:
sparse equality matrix updates can avoid constructing exact zero on a dictionary
MISS/stored-zero/nonzero-multiplier path before existing -product. Round25 skips
conversion on HITS; round96 skips subtraction after conversion; round103 is the
separate doubleton precedent. No new cache/scan/vector; staged updates, represent-
ability, fill caps and original arithmetic stay. Benefit and allocation nonincrease
UNMEASURED; no candidate/admission/integration or automatic rerun prepared.

Master6f68e24/source514/protected6 unchanged;192groups ORsessions/noJulia verified.
PRESOLVE-EXACT-CACHE-PIPELINE current STATUS/roadmap closure/publication/continuation
six SHA bindings map ONLY to this profile's beforecopies; all older mappings stay.
Profile original postcheck report binding maps ONLY report.before-user-correction.md;
recommendation-correction binds corrected report and historical/source reads, not
retroactive launch pins. Frozen raw/scripts/pins/reviews NEVER RERUN/rewrite.
Broader plan OPEN, CIoff,HHdisabled,automationpaused. Any subsequent production
candidate requires its own concrete design/review; no safeguards relaxed.
'''
text=status.read_text();req('## Exact next action\n' in text,'status header');text=text.replace('## Exact next action\n','## Exact next action\n\n'+summary+'\n## Previous exact-conversion cache experiment\n',1);status.write_text(text)
with road.open('a') as f:f.write('\n## Large-model presolver attribution — 2026-10-14\n\n'+summary)
save(D/'continuation.json',dict(all_passed=True,scope='Diagnostic completion with explicit partial medium/test limitations; no optimization acceptance.',previous_binding_map=mapping,sha256={str(p):sha(p) for p in (status,road,D/'continuation-host.json',D/'continuation.py',R/'diagnostics/simplex-core-architecture/PRESOLVE-LARGE-PASS-PROFILE.md')}))
print('Continuation updated; six prior bindings preserved')
