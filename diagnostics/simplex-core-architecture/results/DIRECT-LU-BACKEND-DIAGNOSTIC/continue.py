from pathlib import Path
import sys
E=Path(__file__).resolve().parent;D=E.parent/'DIRECT-LU-BACKEND-PREPARATION';sys.path.insert(0,str(D))
from control import *
v=rd(E/'review.json');req(v['accepted'] is True and v['findings']==[],'Result review rejected')
req(all(sha(Path(n) if Path(n).is_absolute() else R/n)==h for n,h in v['sha256'].items()),'Review binding changed')
s=R/'diagnostics/simplex-core-architecture/STATUS.md';r=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
req(s.read_bytes()==(E/'STATUS.md.before-probe').read_bytes(),'STATUS changed');req(r.read_bytes()==(E/'roadmap.md.before-probe').read_bytes(),'Roadmap changed')
h=host(rd(E/'post-host.json')['groups']);save(E/'continuation-host.json',h)
req(not h['matches'] and all(h[k]==rd(E/'entry-host.json')[k] for k in ('head','master','boot_id')),'Host changed')
t=s.read_text();a=t.index('## Exact next action');z=t.index('## Previous missing-zero experiment',a)
new='''## Exact next action

Direct LU backend diagnostic completed ONCE and independently reviewed.
See DIRECT-LU-BACKEND-DIAGNOSTIC.md and results/DIRECT-LU-BACKEND-DIAGNOSTIC.
The <=45s allowance is CONSUMED: actual6.795441914s inclusive/exit0, canonical
12/12integrity audit PASS, but15/18exact residuals PASS and3FALSE preserved.
Fresh DSE, ordinary post-refactor DSE and direct-base DSE are bit-identical to
one another AND originalcost1step5. Originalcost1FAILED/CONSUMED, cost2BLOCKED.

Fresh B4 exhibits the same error without FT update/refactor history. Both captured
factors agree exceptInfo, do_recip=1,234L/248Uentries. Row87 originalresidual
~6.889312e-11 exceeds originalbound18.8614times. Recorded factorrepresentation
and combinedapplication are both nonzero contributors; this is NOT a captured
native intermediate solve or an identified native operation/rootcause/repair.
No tolerance/control/precision change, no production/candidate modification.
3factorizations/13FTRAN/5BTRAN/4replacements/1refactor/2snapshots,3live nativefactors;
all16resetpredicates/inputs/controls/nativeownership PASS. All206groupsANDsessions
closed/noJulia. Full4749launchpins,514baselinefiles andportable8rawfiles verified.

The bounded diagnostic plan is complete. NEXT permitted direction is a bounded
OFFLINE analysis of the newly saved factor/solution/source evidence to identify
a concrete cause before proposing a repair. Do not rerun this process/auditor,
reopen cost2, tune the benchmark, change tolerance or promote production from
these diagnostic results. Any repair/newnumerics requires its own concrete plan
and independent admission; standing short-run authorization does not waive gates.
Preparation scripts/manifests/reviews, originalfailedcost1 andallolder artifacts
remain FROZEN. Preparation closure/publication currentSTATUS/roadmap bindings map
ONLY to DIAGNOSTIC before-probe copies; allolder mappings unchanged. Master6f68e24
unchanged, CIoff/HHdisabled/automationpaused, broader optimization/fullsuite OPEN.

'''
s.write_text(t[:a]+new+t[z:])
with r.open('a') as f:f.write('''
### Direct LU backend diagnostic result

ONE admitted6.7954s diagnostic reproduced the original DSE error in fresh native
B4, ordinary FT and direct-base solves.15/18residuals PASS,3FALSE preserved;
12/12integrity audit accepted, independent result review complete. Stored factors
and combined application both have nonzero contributions; exact native cause
unresolved. See DIRECT-LU-BACKEND-DIAGNOSTIC.md. Allowance consumed; no rerun,
cost2, automatic repair or promotion. Next bounded offline saved-evidence/source
analysis only, before any concrete repair proposal. Production/master unchanged.
''')
m=[]
for name in ('closure.json','publication.json'):
 rec=rd(D/name)
 for path,before in ((s,E/'STATUS.md.before-probe'),(r,E/'roadmap.md.before-probe')):
  key=str(path.relative_to(R));req(rec['sha256'][key]==sha(before),'Before binding')
  m.append(dict(record=str((D/name).relative_to(R)),key=key,preserved_path=str(before.relative_to(R)),sha256=sha(before)))
save(E/'continuation.json',dict(mappings=m,scope='Only preparation current continuation bindings; all older mappings unchanged'))
with (R/'.superpowers/sdd/2026-10-14-direct-lu-markowitz/progress.md').open('a') as f:f.write('''
- Backend diagnostic ONE6.7954s process after exact independent admission:
  12integritygatesPASS,15/18residualsPASS,3DSEFALSE preserved and bit-identical to
  originalcost1step5 (fresh/ordinary/base).3factor13F5B4replace1refactor2snapshots.
  Representation/application both contribute; native operation cause unresolved.
  Independent resultreview accepted; full4749pins/514baseline/206groups closure.
  Ruling: bounded diagnostic complete, allowance consumed; next offline saved
  factor/source analysis only, no rerun/cost2/automatic repair or promotion.
  Preserve all raw/scripts/workspaces; no generic task-done rerun or cleanup.
''')
print('Continuation updated after fresh206group/session preflight')
