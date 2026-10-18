from pathlib import Path
import json,hashlib
R=Path.cwd();E=Path(__file__).resolve().parent
S=R/'docs/superpowers/specs/2026-10-18-direct-bg-export-workspace.md';P=R/'docs/superpowers/plans/2026-10-18-direct-bg-export-workspace.md'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=json.loads((E/'author-check.json').read_text());v=json.loads((E/'review.json').read_text())
maps={str(S):E/'spec.before-review.md',str(P):E/'plan.before-review.md'}
s=S.read_text();p=P.read_text();old=(E/'spec.before-review.md').read_text()
checks={
 'initial_author_preserved':a['all_passed'] and all(sha(maps.get(n,Path(n)))==h for n,h in a['readtime_sha256'].items()),
 'initial_review_preserved':not v['accepted'] and len(v['findings'])==2 and all(sha(maps.get(n,Path(n)))==h for field in ['readtime_sha256','evidence_sha256'] for n,h in v[field].items()),
 'red_eager_original':'explicit four-buffer parameters' in old and 'accepts only :seen or :orientation' in old,
 'green_staged':'Scratch acquisition is STAGED' in s and 'Only after that guard succeeds acquire permuted and transformed' in s,
 'atomic_retention':'atomically attach all four if eligible' in s and 'never retains a partial pair' in s,
 'early_budget':'only two length-n Float64 arrays (16*n payload)' in s and 'requests four (32*n)' in s,
 'early_controls':'orientation_staged_early_exit' in p and 'cold/nonretained orientation early exit' in p,
 'offdiagonal_controls':'normalization_rejection_first_middle_last_offdiagonal' in p and 'finite nonzero D/D=1 cannot trigger' in s,
 'scope_unchanged':'No Julia/query/parser/import/compile' in s and not (R/'diagnostics/direct-bg-export-workspace').exists(),
 'read_only_raw_and_private_publish':'no write to raw U.nzval' in s and 'preserve active inner identity' in s,
}
paths=[S,P,E/'spec.before-review.md',E/'plan.before-review.md',E/'author-check.json',E/'review.json',E/'review.md',E/'reviewer-check.py',E/'reviewer-check.json',Path(__file__).resolve()]
out=dict(all_passed=all(checks.values()),checks=checks,before_mapping={n:str(q) for n,q in maps.items()},readtime_sha256={str(q):sha(q) for q in paths},scope='Offline document amendment only, original checks and rejected review preserved; no Julia')
with (E/'amendment-check.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=out['all_passed'],checks=len(checks),bindings=len(paths),failed=[k for k,v in checks.items() if not v])))
if not out['all_passed']:raise SystemExit(1)
