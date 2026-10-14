from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd();B=R/'diagnostics/simplex-core-architecture';D=B/'results/MA-Y-FALLBACK';Y=B/'results/MA-Y'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
maps=rd(D/'continuation-map.json')['old_bindings'];mapping={m['path']:m['preserved'] for m in maps}
h=rd(D/'host.json');analysis=rd(D/'analysis.json');review=rd(D/'review.json');continuation=rd(D/'continuation.json')
checks=dict(
 independent_checker=rd(D/'review-check.json')['accepted'] is True and rd(D/'review-check.json')['qualification_accepted'] is False and all(rd(D/'review-check.json')['checks'].values()) and rd(D/'review-check.json')['failures']==analysis['original_failures'] and all(sha(p)==v for p,v in rd(D/'review-check.json')['sha256'].items()),
 independent_review=review['accepted'] is True and review['findings']==[],
 review_bindings=all(sha(p)==v for p,v in review['sha256'].items()),
 analysis20=analysis['all_passed'] is True and len(analysis['checks'])==20 and all(analysis['checks'].values()),
 analysis36=all(sha(p)==v['sha256'] for p,v in analysis['readtime_pins'].items()) and len(analysis['readtime_pins'])==36,
 qualification_still_rejected=analysis['qualification_accepted'] is False and rd(Y/'closure.json')['qualification_accepted'] is False,
 continuation=continuation['all_passed'] is True and all(sha(p)==v for p,v in continuation['sha256'].items()),
 exact_six_maps=len(maps)==6 and all(sha(m['preserved'])==m['sha256']==rd(m['source'])['sha256'][m['path']] for m in maps),
 priorYclosure=all(sha(mapping.get(p,p))==v for p,v in rd(Y/'closure.json')['sha256'].items()),
 priorYpublication=all(sha(mapping.get(p,p))==v for p,v in rd(Y/'publication.json')['sha256'].items()),
 old_publication_file=sha(Y/'publication.json')==rd(D/'entry.json')['sha256'][str(Y/'publication.json')],
 source514=all(sha(R/p)==v for p,v in h['master_identity'].items()) and len(h['master_identity'])==514,
 protected6=all(sha(p)==v for p,v in h['protected'].items()) and len(h['protected'])==6,
 refs=git('rev-parse','HEAD')==h['refs']['head'] and git('rev-parse','master')==h['refs']['master'],
 tracked_scope=set(git('diff','--name-only','HEAD').splitlines())==set(str(Path(p).relative_to(R)) for p in mapping),
 no_stage=not git('diff','--cached','--name-only'),
 no_aggregate=not (B/'results/MA-X/aggregate.json').exists())
if not all(checks.values()):raise SystemExit(str(checks))
paths=sorted(p for p in D.iterdir() if p.is_file())+[B/'MA-DENSELU-COMPLETE-FALLBACK-ANALYSIS.md',B/'STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
obj=dict(all_passed=True,qualification_accepted=False,checks=checks,sha256={str(p):sha(p) for p in paths})
with (D/'closure.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
print('Closure:',len(checks),'PASS;',len(paths),'bindings')
