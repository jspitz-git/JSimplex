"""Publish the reviewed allowance once; never launches Julia."""
from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/S2-E';D=E.parent/'S2-D'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def require(v,s):
 if not v:raise ValueError(s)
a=read(E/'allowance-proposal.json');review=read(E/'admission-review-check.json')
require(review['accepted'] is True and review['all_passed'] is True and review['unresolved_findings']==[] and all(review['checks'].values()),'independent admission rejected')
require('ACCEPTED S2-D numerical admission.' in (D/'numerical-review.md').read_text(),'missing exact literal acceptance')
require(all(sha(p)==h for p,h in review['sha256'].items()),'review bindings changed')
require(all(sha(p)==h for p,h in a['sha256'].items()),'proposal bindings changed')
require(a['refs']=={str(p):subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip() for p in [R,Path('/home/jspitz/JSimplex.jl')]},'refs changed')
require(sha(D/'launch-pins.json')==a['pins_sha256'],'manifest changed')
pins=read(D/'launch-pins.json');require(all(sha(p)==v['sha256'] and str(Path(p).resolve(strict=True))==v['resolved'] for p,v in pins['inventory'].items()),'launch inventory changed')
for p in [D/'numerical-review.md',E/'admission-review-check.json']:
 a['sha256'][str(p)]=sha(p)
with (D/'allowance.json').open('x') as f:json.dump(a,f,indent=2);f.write('\n')
with (E/'seal.json').open('x') as f:json.dump({'all_passed':True,'proposal_unchanged_except_two_review_bindings':True,'sha256':{str(p):sha(p) for p in [E/'seal.py',E/'allowance-proposal.json',D/'launch-pins.json',D/'allowance.json',D/'numerical-review.md',E/'admission-review-check.json']}},f,indent=2);f.write('\n')
print('Allowance sealed; no launch performed.')
