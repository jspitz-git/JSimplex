"""Separate one-shot closure for reviewed publication-only whitespace exception."""
from pathlib import Path
import json,hashlib,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3]
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bound(z):return all(sha(Path(n) if Path(n).is_absolute() else R/n)==v for n,v in z['sha256'].items())
def require(x,m):
 if not x:raise RuntimeError(m)
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
review=rd(D/'publication-review.json');initial=rd(D/'closure.json');mainreview=rd(D/'review-final.json')
checks=dict(initial_closure=initial['all_passed'] is True and bound(initial),main_review=mainreview['accepted'] is True and bound(mainreview),supplement_review=review['accepted'] is True and review['findings']==[] and review['scope']=='exact diff-context publication' and bound(review),pins=bound(rd(D/'preparation-pins.json')),old_failure_preserved=rd(D/'publication-failure.json')['failed_subcommand_returncode']==2 and not (D/'publication.json').exists(),no_new_run=not (D/'runs').exists() and not (R/'.superpowers/native-pivot-green2/green2').exists(),refs=git('rev-parse','HEAD')=='30b0b3402ef5d319c8faa0a78aca32ca3c354d22' and git('rev-parse','master')=='6f68e24e8ddac42b948da8fcc2d636c010751194')
old=rd(D/'publication-names.json')['names'];checks['original_partial_index']=set(git('diff','--cached','--name-only').splitlines())==set(old)-{str((D/'publication.json').relative_to(R))}
names=rd(D/'publication-names-final.json')['names'];own=str((D/'closure-supplement.json').relative_to(R));pub=str((D/'publication-final.json').relative_to(R))
actual={str(p.relative_to(R)) for p in D.rglob('*') if p.is_file()}|{own,pub,'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'}
checks['exact_final_names']=set(names)==actual and len(names)==len(actual)
require(all(checks.values()),str(checks))
with (D/'closure-supplement.json').open('x') as f:json.dump(dict(all_passed=True,checks=checks,sha256={n:sha(R/n) for n in names if n not in [own,pub]},scope='Separate publication-only closure; old12PASS closure and failedpublication unchanged'),f,indent=2);f.write('\n')
print(dict(checks=len(checks),bindings=len(names)-2,all_passed=True))
