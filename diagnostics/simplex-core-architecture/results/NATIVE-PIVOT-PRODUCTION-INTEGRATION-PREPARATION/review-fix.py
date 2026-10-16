"""One separate plan-only amendment; preserves initial review and plan bytes."""
from pathlib import Path
import json,hashlib
Q=Path(__file__).resolve().parent;R=Q.parents[3];P=R/'docs/superpowers/plans/2026-10-16-native-pivot-production-integration.md'
def need(v,m):
 if not v:raise RuntimeError(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
need((Q/'review-initial.json').exists(),'Initial review must be recorded first')
old=P.read_text();before=Q/'plan.before-review.md'
with before.open('xb') as f:f.write(P.read_bytes())
a='- [ ] Freeze 300s first-run command/pins and obtain fresh gpt-6-astra exact-stage\n  admission before execution. Concrete executable driver/auditor/guard publication\n  must exist, not merely this plan. Reserve prospective600s policy now; a retry\n  still needs its own immutable output path, fresh refs/process checks, source-\n  identical seal and independent exact admission. No further human permission needed.'
b='- [ ] Freeze the prospective300s command and production-commit preparation, and\n  obtain fresh gpt-6-astra readiness review before local master fast-forward. This\n  pre-FF review accepts commit/application preparation ONLY; it is NOT launch\n  admission for an actual-master run. Concrete executable driver/auditor/guard\n  publication must exist, not merely this plan. Reserve prospective600s policy now;\n  each attempt needs its own immutable output path and final actual-master seal\n  with independent exact-stage acceptance as required by Task3. No further human permission needed.'
c='- [ ] Seal actual master refs, source hashes and command immediately before the\n  one300s focused run. The actual loaded JSimplex must be that master source tree.'
d='- [ ] AFTER the local master fast-forward, seal the actual master refs, source\n  hashes, command, runtime/environment, output reservation and current host state.\n  Obtain fresh independent gpt-6-astra exact-stage acceptance of THIS final\n  actual-master seal BEFORE any Julia launch. Pre-FF readiness acceptance alone\n  never authorizes launch; any later ref/source/environment change requires a new\n  seal and review. Apply this same post-FF actual-master sealing and acceptance\n  requirement to the separately labelled600s pure-timeout attempt. Only then run\n  the one300s focused attempt (or the admitted600s repeat). The actual loaded\n  JSimplex must be that master source tree.'
need(old.count(a)==1 and old.count(c)==1,'Exact amendment anchors')
red='acceptance of THIS final\n  actual-master seal BEFORE any Julia launch' in old
new=old.replace(a,b).replace(c,d);P.write_text(new)
need(not red and 'acceptance of THIS final\n  actual-master seal BEFORE any Julia launch' in new,'RED/GREEN')
plan_key=str(P.relative_to(R));author=json.loads((Q/'author-check.json').read_text());need(author['sha256'][plan_key]==sha(before),'Old author plan binding')
for n,h in author['sha256'].items():need(sha(before if n==plan_key else R/n)==h,'Original author binding '+n)
record=dict(all_passed=True,checks=dict(red_missing_actual_master_review=not red,exact_two_replacements=True,green_actual_master_launch_review=True,green_retry_same_requirement=True,initial_review_preserved=True,original_author26_reconciled=True),mapping=dict(record=str((Q/'author-check.json').relative_to(R)),key=plan_key,sha256=sha(before),preserved=str(before.relative_to(R))),sha256={str(p.relative_to(R)):sha(p) for p in [P,before,Path(__file__),Q/'review-initial.json',Q/'author-check.json']})
save(Q/'review-fix.json',record)
print('Plan amendment6PASS; original author26 bindings preserved')
