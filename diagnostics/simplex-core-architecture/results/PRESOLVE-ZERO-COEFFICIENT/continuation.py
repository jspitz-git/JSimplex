from pathlib import Path
import sys
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/PRESOLVE-ZERO-COEFFICIENT');sys.path.insert(0,str(D));from control import *
P=D.with_name('PRESOLVE-LARGE-PROFILE');groups=rd(D/'green2-posthost.json')['groups'];h=host(groups);save(D/'continuation-host.json',h);entry=rd(D/'host.json');req(not h['matches'] and all(h[k]==entry[k] for k in ('head','master','boot_id')),'fresh host')
status=R/'diagnostics/simplex-core-architecture/STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';mapping={}
for current,before in [(status,D/'STATUS.md.before-zero'),(road,D/'roadmap.md.before-zero')]:
 req(current.read_bytes()==before.read_bytes(),'before text changed')
 for n in ('closure.json','publication.json','continuation.json','result-review.json'):
  doc=rd(P/n)
  if str(current) in doc.get('sha256',{}):
   val=doc['sha256'][str(current)];req(val==sha(before),'prior binding')
   mapping[str(P/n)+'::'+str(current)]=dict(preserved=str(before),sha256=val)
summary='''Missing-zero sparse-equality candidate tested; **REJECTED for allocation increase**.
See PRESOLVE-ZERO-COEFFICIENT.md and results/PRESOLVE-ZERO-COEFFICIENT. Actual
production/test/env/master remain unchanged at master6f68e24. Float64-only sentinel
candidate has exact two-fragment inverse; generic precisions retain original path.
RED expected count1 versus0:2PASS/1expectedFAIL; GREEN5,155focused assertions PASS.
Nine synthetic cases3warm+8measured pairs each,99pairs/198scheduled aggregate calls;
all measured144windows compile/recompile0, all saved results/inputowners equal.
Four signed targets remove768events/128updates and~1.5%bytes, but nonzero control
adds512events/18,432median bytes, zero multiplier384/14,352,dense36/1,296. No
allocation-noise waiver; no universal time/full-presolve speedup. Compiler cause
UNPROVED. Exact implementation is not promotable; no second variant or rerun.

GREEN then failed before ANY Netlib measurement: new driver erroneously supplied
unsupported native_reader keyword to read_mps. Exit1/no finalraw/launcher missingraw
failure preserved. partial-analysis reconciles saved subset ONLY, not full PASS.
No whole-presolve/large-model candidate measurement; fixing reader cannot rescue
known cost rejection. Two short processes only, no old numerical/auditor reruns.
Initial RED/GREEN admission rejections and separate corrections all preserved.

Prior profile current STATUS/roadmap bindings map ONLY to zero experiment before-
zero copies, explicitly recorded in continuation.json. All older mappings stay.
Candidate/drivers/pins/raw/reviews FROZEN. Further work needs a genuinely different
concrete implementation/admission; never repeat propagation or this frozen attempt
as an equivalent next step. Broader plan OPEN, CIoff/HHdisabled/automationpaused.
'''
s=status.read_text();start=s.index('## Exact next action\n')+len('## Exact next action\n');end=s.index('\n## ',start)
status.write_text(s[:start]+'\n'+summary+s[end:])
s=road.read_text();pos=s.index('\n')+1;road.write_text(s[:pos]+'\n## 2026-10-14 missing-zero candidate decision\n\n'+summary+'\n'+s[pos:])
save(D/'continuation.json',dict(previous_binding_map=mapping,sha256={str(p):sha(p) for p in [status,road,D/'STATUS.md.before-zero',D/'roadmap.md.before-zero',R/'diagnostics/simplex-core-architecture/PRESOLVE-ZERO-COEFFICIENT.md']},scope='Only diagnostic rejection; broader plan open, prior evidence unchanged.'))
print('Continuation updated;',len(mapping),'exact previous bindings preserved')
