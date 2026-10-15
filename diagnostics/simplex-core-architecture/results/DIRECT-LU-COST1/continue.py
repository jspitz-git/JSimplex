from pathlib import Path
import sys
A=Path(__file__).resolve().parent.parent/'DIRECT-LU-COST-PREPARATION'
sys.path.insert(0,str(A))
from control import rd,sha,save,req,host,git,R
B=Path(__file__).resolve().parent

review=rd(B/'review.json')
req(review['accepted'] is True and review['findings']==[],'Result review rejected')
req(all(sha(Path(n) if Path(n).is_absolute() else R/n)==h for n,h in review['sha256'].items()),'Review binding changed')
status=R/'diagnostics/simplex-core-architecture/STATUS.md'
road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
req(status.read_bytes()==(B/'STATUS.md.before-cost1').read_bytes(),'STATUS changed')
req(road.read_bytes()==(B/'roadmap.md.before-cost1').read_bytes(),'Roadmap changed')
fresh=host(rd(B/'final-host.json')['groups']);save(B/'publication-prehost.json',fresh)
req(not fresh['matches'] and len(fresh['groups'])==204,'Host not clear')
req(all(fresh[k]==rd(B/'final-host.json')[k] for k in ('head','master','boot_id')),'Refs or boot changed')
s=status.read_text();start=s.index('## Exact next action');end=s.index('## Previous missing-zero experiment',start)
new="""## Exact next action

Direct LU / Markowitz Task 3 cost1 executed once and STOPPED on correctness.
Numerical/cost qualification NOT ACCEPTED; reservation CONSUMED; cost2 BLOCKED.
See DIRECT-LU-COST1.md and results/DIRECT-LU-COST1/review.md. Independent result
review accepts the diagnostic rejection only. Canonical false audit, exit 2 and
all partial raw records are frozen. No retry, tuning or automatic promotion.

The 12.8165 s inclusive process returned 241 lifecycle windows / 12 complete cells.
The first warm ordinary REFERENCE sparse96 / FT / native window fails four DSE
residual checks after refactor 1 (steps 5–8): exact residual/bound = 18.861415966.
Input tokens and ordinary modes match. All 5,760 outputs in completed n32 cells
pass; the partial exact census totals 5,780/5,784. Candidate sparse96 never ran.
All 12 completed cells have slower medians and higher allocation bytes/events;
smaller final reachable graphs do not rescue the fixed cost gates. These partial
first-process n32 measurements do not establish a universal performance claim.

Next concrete step: bounded SOURCE/saved-evidence diagnosis of ordinary sparse96
FT/native DSE residuals after the first refactor, without numerical replay or
changing tolerances. Specific internal cause remains unproved. Any subsequent
numerical attempt requires its own frozen admission; existing cost2 cannot run.
Task 1–2 corrected GREEN remains scoped to earlier accepted fixtures (19,557 PASS).
Production/master 6f68e24 unchanged; CI off, automation paused, HH reuse disabled.
Broader programme remains open. All earlier evidence and before mappings remain.
Preparation closure/publication current STATUS/roadmap bindings resolve ONLY to
DIRECT-LU-COST1 before-cost1 copies; stage review's textual STATUS hash does too.

"""
status.write_text(s[:start]+new+s[end:])
with road.open('a') as f:f.write("""
### Direct LU Task 3 first cost process: diagnostic rejection

One independently admitted cost1 process stopped after 12.8165 s inclusive:
241 windows, 12 complete n32 cells; first warm ordinary sparse96 FT/native DSE
residual fails the frozen bound at steps 5–8. No retry or cost2. All completed
n32 cells have slower medians and more allocation bytes/events, with smaller
reachable factor graphs. Partial data are descriptive, not a cost qualification.
See diagnostics/simplex-core-architecture/DIRECT-LU-COST1.md and its review.
Next bounded work is source/saved-evidence diagnosis; no numerical replay,
threshold changes or promotion. Production defaults and all older gates remain.
""")
with (R/'.superpowers/sdd/2026-10-14-direct-lu-markowitz/progress.md').open('a') as f:f.write("""
- Task 3 cost1: exact independent stage admission, ONE 12.8165 s process, exit 2.
  241 windows / 12 complete cells; ordinary sparse96 FT/native DSE residuals fail
  at steps 5–8. Canonical audit FALSE preserved; attempt consumed, cost2 blocked.
  New exact partial analysis 5,780/5,784 pass; no rerun. Completed n32 cells slower
  and more allocating, smaller retained graph. Independent diagnostic result review
  accepted. Next source/saved-evidence diagnosis only, no automatic numerical work.
""")
print('Continuation updated; failed cost1 remains failed and cost2 blocked')
