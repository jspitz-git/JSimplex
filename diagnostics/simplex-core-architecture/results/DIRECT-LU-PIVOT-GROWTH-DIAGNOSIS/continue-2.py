from common import *
v=rd(F/'review.json');req(v['accepted'] is True and v['findings']==[] and bindings(v),'Review rejected or changed')
amend=rd(F/'publication-amendment-review.json');req(amend['accepted'] is True and amend['findings']==[] and bindings(amend),'Publication amendment rejected or changed')
s=R/'diagnostics/simplex-core-architecture/STATUS.md';r=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
req(s.read_bytes()==(F/'STATUS.md.before-growth').read_bytes(),'STATUS changed');req(r.read_bytes()==(F/'roadmap.md.before-growth').read_bytes(),'Roadmap changed')
h=host();save(F/'continuation-host.json',h);req(not h['matches'] and len(h['groups'])==206,'Active historical groups/session or Julia')
req(all(h[k]==rd(F/'entry-host.json')[k] for k in ('head','master','boot_id')),'Refs/boot changed')
m=[]
for name in ('closure.json','publication.json'):
 rec=rd(E/name)
 for p,b in ((s,F/'STATUS.md.before-growth'),(r,F/'roadmap.md.before-growth')):
  k=str(p.relative_to(R));req(rec['sha256'][k]==sha(b),'Previous continuation binding')
  m.append(dict(record=str((E/name).relative_to(R)),key=k,preserved_path=str(b.relative_to(R)),sha256=sha(b)))
save(F/'continuation.json',dict(mappings=m,scope='Only backend diagnostic current STATUS/roadmap closure/publication bindings; all older mappings unchanged'))
t=s.read_text();a=t.index('## Exact next action');z=t.index('## Previous missing-zero experiment',a)
new='''## Exact next action

Direct LU saved-factor growth diagnosis completed OFFLINE and independently
reviewed. See DIRECT-LU-PIVOT-GROWTH-DIAGNOSIS.md and its results directory.
The saved native sparse96 B4 factors exhibit max U231235.789 versus max B4=4,
final-factor growth245688.026 relative to scaled input. Despite exact input
cond_inf<=153/103, factor position(31,31), original(87,1), cancels terms of total
absolute magnitude462471.58 to -53/2^42 rather than zero. Actual unsymmetric
strategy/pivot tolerance0.1/IRSTEP0; RCOND4.5522e-7 is a U-diagonal ratio, not
an exact input condition estimate. Growth/cancellation is the concrete numerical
mechanism; native rounding sequence/pivot candidate decisions remain uncaptured.
Representation AND combined application contributions remain nonzero.

No new Julia/native/solve/measurement or production/test/env/CI changes. New exact
saved-data analysis20checks and author10checks PASS. Its initial provenance-path
failure is preserved separately; no old script/auditor rerun. Prior backend
allowance CONSUMED,15/18residualsPASS and3FALSE; originalcost1FAILED/CONSUMED,
cost2BLOCKED. No threshold/tolerance/precision tuning or candidate promotion.

NEXT proposed concrete work is a separate SOURCE/DESIGN plan for an explicit
native Float64 accuracy policy at factor construction: compare the rationale and
cost obligations of stronger pivot acceptance versus iterative refinement, with
ownership/copy/refactor propagation, fill/solve scratch and memory accounted.
Preserve defaults initially; freeze correctness/cost scope and independent review
before any numerical execution. This is not an admitted repair, a promised fix,
a cost1 rerun or automatic cost2 permission. Do not create another equivalent
saved-factor inventory. The original direct-LU comparison remains incomplete.

Backend diagnostic closure/publication currentSTATUS/roadmap bindings map ONLY to
PIVOT-GROWTH-DIAGNOSIS before-growth copies; all older mappings unchanged. All old
raw/scripts/reviews/pins remain FROZEN. Master6f68e24 unchanged, CIoff/HHdisabled,
automationpaused, broader optimization/fullsuite OPEN.

'''
s.write_text(t[:a]+new+t[z:])
with r.open('a') as h:h.write('''
### Direct LU saved-factor growth diagnosis

Bounded offline analysis identifies final U growth245688 versus scaled B4 despite
cond_inf<=153/103. Factor(31,31) cancels three large products to -53/2^42 instead
of zero; original row87 residual and both representation/application terms match
the preserved diagnostic. Actual unsymmetric/pivot0.1/IRSTEP0; no new solve or
measurement. See DIRECT-LU-PIVOT-GROWTH-DIAGNOSIS.md. Next: separate source/design
accuracy-policy plan with pivot/refinement work, fill, scratch and ownership
obligations. No admitted remedy or automatic numerical permission; cost1 failed,
cost2 blocked, default controls and all frozen evidence unchanged.
''')
with (R/'.superpowers/sdd/2026-10-14-direct-lu-markowitz/progress.md').open('a') as h:h.write('''
- Saved-factor growth diagnosis OFFLINE: maxU231235.789/scaled growth245688,
  exactcond<=153/103; row31,col31 cancellation -53/2^42 at original87,1.
  Both old representation/application contributions retained. Actual unsymmetric
  pivot0.1/IRSTEP0.20analysis+10author checks, fresh independent review accepted.
  No new Julia/solver/benchmark, no old rerun; initial provenance path failure
  preserved with separate one-filename fix. Next separate source/design accuracy
  policy plan only; no admitted remedy/cost2/promotion, original comparison open.
''')
print('Continuation updated after fresh206group/session preflight')
