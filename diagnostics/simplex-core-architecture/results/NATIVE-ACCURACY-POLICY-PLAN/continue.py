from common import *
v=rd(F/'review.json');req(v['accepted'] is True and v['findings']==[] and bindings(v),'Review rejected or changed')
s=R/'diagnostics/simplex-core-architecture/STATUS.md';r=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
req(s.read_bytes()==(F/'STATUS.md.before-policy').read_bytes(),'STATUS changed');req(r.read_bytes()==(F/'roadmap.md.before-policy').read_bytes(),'Roadmap changed')
h=host();save(F/'continuation-host.json',h);req(not h['matches'] and len(h['groups'])==206,'Active prior groups/session or Julia');req(all(h[k]==rd(F/'entry-host.json')[k] for k in ('head','master','boot_id')),'Refs/boot changed')
m=[]
for name in ('closure.json','publication.json'):
 for p,b in ((s,F/'STATUS.md.before-policy'),(r,F/'roadmap.md.before-policy')):
  k=str(p.relative_to(R));req(rd(E/name)['sha256'][k]==sha(b),'Previous continuation binding')
  m.append(dict(record=str((E/name).relative_to(R)),key=k,preserved_path=str(b.relative_to(R)),sha256=sha(b)))
save(F/'continuation.json',dict(mappings=m,scope='Only pivot-growth current STATUS/roadmap closure/publication bindings; all earlier mappings unchanged'))
t=s.read_text();a=t.index('## Exact next action');z=t.index('## Previous missing-zero experiment',a)
new='''## Exact next action

Native Float64 accuracy-policy comparison plan independently accepted SOURCE/DESIGN
ONLY. Plan: docs/superpowers/plans/2026-10-15-native-float64-accuracy-policy.md;
evidence results/NATIVE-ACCURACY-POLICY-PLAN. No new Julia/numerics/candidate/driver
or production/test/env/CI/master changes in this planning step.

NEXT permitted work is Task1 OFFLINE preparation of the private component driver,
fixed inputs/schema, fail-closed auditor and launcher, with independent review.
This does not launch Julia. Only then seal and independently accept the exact
Task2 stage before ONE <=45s process using existing standing short-run permission.
No new human permission question is needed solely to repeat the granted allowance;
concrete admission, resources, fresh host/refs and one-attempt gates still apply.

Three frozen arms: C pivot0.1/IRSTEP0, P pivot1/IRSTEP0, R pivot0.1/IRSTEP2.
Four saved sparse/dense32/96 B4 cases;3warm8measured rounds,132cost windows.
Whole proposed call budget141freshLU/9lu!attempts/3shallowcopies/4245F+2133B,
12finalfactor snapshots; these are entries, not a complete native/import budget.
R retains4n additionalFloat64 workspace elements (32n payload bytes). Per-call
attempted/taken refinement metadata, constructor and solve costs, all output bits,
fill and memory are recorded separately. Same original128*n*eps residual bound.
No arm is presumed to repair the error; no combined arm or post-result tuning.

Saved growth diagnosis remains accepted: scaled finalU growth245688.026 despite
cond_inf<=153/103, cancellation -53/2^42 at factor31,31/original87,1; both old
representation/application contributions retained. No exact native rounding trace.
Originalcost1FAILED/CONSUMED, cost2BLOCKED, old diagnostic allowanceCONSUMED.
This is a separate policy experiment, not an automatic benchmark retry or remedy.
Production defaults and manager propagation stay unchanged; subsequent integration
would require its own ownership/copy/spare/failure design and qualification.

Pivot-growth closure/publication currentSTATUS/roadmap bindings map ONLY to
NATIVE-ACCURACY-POLICY-PLAN before-policy copies; all earlier mappings unchanged.
All older raw/scripts/pins/reviews/plans FROZEN. Master6f68e24 unchanged,
CIoff/HHdisabled/automationpaused; originaldirectLUcomparison/fullsuite remainOPEN.

'''
s.write_text(t[:a]+new+t[z:])
with r.open('a') as h:h.write('''
### Native Float64 accuracy-policy comparison plan

SOURCE/DESIGN plan accepted; no new numerical execution. See
2026-10-15-native-float64-accuracy-policy.md. Next Task1 OFFLINE concrete driver,
inputs, auditor and launcher preparation with independent review. Three fixed
native arms compare current0.1/0, pivot1/0 and refinement0.1/2; same frozen
sparse/dense32/96 inputs and original residual bound. Constructor/solve costs,
R extra32n workspace bytes and native refinement attempts are explicit. Future
one<=45s experiment needs exact independent admission. No default change,
production propagation, oldcost1 rerun or cost2/promotion permission follows.
''')
with (R/'.superpowers/sdd/2026-10-14-direct-lu-markowitz/progress.md').open('a') as h:h.write('''
- Native Float64 accuracy-policy SOURCE/DESIGN plan accepted independently:
  fixedC(.1,0)/P(1,0)/R(.1,2), unchanged bound; 4savedfixtures,3warm8measured,
  141freshLU9lu!3copy6378solves,12snapshots future budget. R+32n workspace bytes.
  Next Task1 offline concrete driver/auditor/launcher preparation and review only;
  future ONE<=45s stage requires fresh exact admission, no automatic launch.
  Originalcost1failed/cost2blocked; no production/default/master/CI changes.
''')
print('Continuation updated after fresh206groups/sessions preflight')
