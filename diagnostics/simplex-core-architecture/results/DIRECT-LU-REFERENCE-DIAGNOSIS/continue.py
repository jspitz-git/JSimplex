from pathlib import Path
import sys,json,subprocess,hashlib,ast
D=Path(__file__).resolve().parent;A=D.parent/'DIRECT-LU-COST-PREPARATION';B=D.parent/'DIRECT-LU-COST1'
sys.path.insert(0,str(A))
from control import R,sha,rd,req,save,host,git

v=rd(D/'review.json');req(v['accepted'] is True and v['findings']==[],'Review rejected')
req(all(sha(Path(n) if Path(n).is_absolute() else R/n)==h for n,h in v['sha256'].items()),'Review binding changed')
s=R/'diagnostics/simplex-core-architecture/STATUS.md';r=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
req(s.read_bytes()==(D/'STATUS.md.before-diagnosis').read_bytes(),'STATUS changed');req(r.read_bytes()==(D/'roadmap.md.before-diagnosis').read_bytes(),'Roadmap changed')
h=host(rd(D/'host.json')['groups']);save(D/'continuation-host.json',h)
req(not h['matches'] and all(h[k]==rd(D/'host.json')[k] for k in ('head','master','boot_id')),'Host changed')
t=s.read_text();a=t.index('## Exact next action');z=t.index('## Previous missing-zero experiment',a)
new="""## Exact next action

Direct LU reference source/saved-evidence diagnosis completed and independently
reviewed. See DIRECT-LU-REFERENCE-DIAGNOSIS.md and its results directory.
No Julia or new factor/solve calls. Task 3 cost1 remains FAILED and CONSUMED;
cost2 BLOCKED. Old raw, false audit and partial n32 cost rejections are unchanged.

Source reconstruction localizes the first failed step-5 ordinary FT/native DSE
output to the fresh UMFPACK backend boundary: after refactor 1 the outer history,
upper and maps reset, so post-backend work is identity/prepared copies only.
This is not captured native-factor causality. Exact saved-input dominance proves
kappa_inf <= 153/103; ill-conditioning is not a sufficient explanation. Row 87
and its three solution tokens are unchanged at steps 5–8. Native representation
versus solve-application error remains unresolved; no production fix accepted.

Next: prepare the separate driver and admission under
2026-10-15-direct-lu-reference-backend-diagnostic.md, then independent review.
Prospective ONE <=45 s process compares fresh B4 backend with original prefix
plus refactor, total 3 factorizations, 13 FTRAN, 5 BTRAN, 4 replacements and
1 refactor, two final factor snapshots. No launch until concrete immutable
preparation and exact stage admission pass. No benchmark retry, new tolerance,
control change, candidate tuning or automatic promotion. Production/master
6f68e24 unchanged; CI off, HH reuse disabled, automation paused, broader plan open.
Prior cost1 closure/publication current STATUS/roadmap bind ONLY new before-
diagnosis copies. All older mappings/failures remain. New original analysis17/18
pin-schema failure and separate four-gate pin supplement are preserved.

"""
s.write_text(t[:a]+new+t[z:])
with r.open('a') as f:f.write("""
### Direct LU reference residual source diagnosis

Source/saved-evidence analysis localizes the first post-refactor DSE error to the
ordinary native backend boundary; exact kappa_inf bound is 153/103. No Julia/new
solve, no production fix. Representation versus application remains unobserved.
See DIRECT-LU-REFERENCE-DIAGNOSIS.md. Next prepare the separately reviewed <=45 s
backend diagnostic plan, not cost2 or a benchmark retry. All old evidence stays.
""")
with (R/'.superpowers/sdd/2026-10-14-direct-lu-markowitz/progress.md').open('a') as f:f.write("""
- Post-cost1 source/saved-evidence diagnosis: identity wrapper at first failed DSE
  localizes source-supported backend boundary; kappa_inf <=153/103. No native
  cause/repair claimed. No Julia or repeated benchmark. New analysis17/18 retained
  (inventory object compared with SHA); separate pin-schema supplement passed.
  Ruling: next prepare bounded backend diagnostic, not repeat cost1/cost2; native
  metadata missing, so attribution requires separately admitted new evidence.
  Cost of this ruling: one future bounded diagnostic may not reproduce failure.
""")
print('Continuation updated; diagnostic driver preparation next, no launch')
