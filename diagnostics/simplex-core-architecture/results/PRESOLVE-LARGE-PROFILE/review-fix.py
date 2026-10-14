from control import *
import tomllib
p=R/'diagnostics/simplex-core-architecture/PRESOLVE-LARGE-PASS-PROFILE.md';before=p.read_text();old='Allocation events/bytes for these passes match\nacross repeats.';new='Allocation event counts for these passes match across repeats; bytes vary\nslightly (sparse aggregation 606,302,792 vs 606,325,576; propagation\n659,553,376 vs 659,519,664 bytes). No byte-invariance claim follows.'
req(old in before,'expected report statement')
ws=[tomllib.loads(q.read_text()) for q in (D/'run-1').glob('finish-*.toml')]
checks={};sums={}
for index in (4,8):
 for rep in (2,3):sums[f'{index}/{rep}']={k:sum(w[k] for w in ws if w['index']==index and w['rep']==rep) for k in ('bytes','events')}
 checks[f'old_byte_equality_false_{index}']=sums[f'{index}/2']['bytes']!=sums[f'{index}/3']['bytes']
 checks[f'event_equality_true_{index}']=sums[f'{index}/2']['events']==sums[f'{index}/3']['events']
with (D/'report.before-review.md').open('x') as f:f.write(before)
p.write_text(before.replace(old,new))
checks['old_claim_removed']=old not in p.read_text();checks['exact_new_statement']=new in p.read_text()
req(all(checks.values()),'fix checks')
save(D/'review-fix.json',dict(all_passed=True,checks=checks,sums=sums,previous_report_bindings_map_only_to=str(D/'report.before-review.md'),affected_binding_records=[str(D/'recommendation-correction.json'),str(D/'continuation.json')],sha256={str(q):sha(q) for q in (p,D/'report.before-review.md',D/'review-fix.py')}))
print(len(checks),'offline review-fix checks PASS; no measurement rerun')
