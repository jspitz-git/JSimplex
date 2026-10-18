"""One separate publication correction; preserve original closure, failure and CSV."""
from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-COST1'
def need(v,m):
 if not v:raise RuntimeError(m)
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text())
names=rd(E/'publication-names-final.json')['names'];out=str((E/'publication-final.json').relative_to(R));prior=[n for n in names if n!=out]
old=rd(E/'closure.json');need(old['all_passed'] and len(old['checks'])==19,'original closure')
need(all(sha(R/n)==h for n,h in old['sha256'].items()),'original 236 bindings')
review=rd(E/'publication-fix-review.json');need(review['accepted'] is True and review['findings']==[],'fix review')
need(all(sha(R/n)==h for n,h in review['sha256'].items()),'fix review bindings')
csv=E/'summary.csv';raw=csv.read_bytes();need(raw.count(b'\r\n')==9 and raw.count(b'\r')==9 and raw.count(b'\n')==9,'exact nine CRLF rows')
need(all(line.rstrip(b' \t')==line for line in raw.split(b'\r\n')),'no actual trailing spaces/tabs')
oldnames=rd(E/'publication-names.json')['names'];missing=str((E/'publication.json').relative_to(R))
need(not (R/missing).exists(),'original publication unexpectedly exists')
need(set(git('diff','--cached','--name-only').splitlines())==set(oldnames)-{missing},'unchanged original stage')
run=E.parent/'DIRECT-BG-SPLIT-COST-PREPARATION/runs/cost1-300'
actual={str(p.relative_to(R)) for root in (E,run) for p in root.rglob('*') if p.is_file()}
need(len(names)==len(set(names)) and actual==set(prior),'exact final scope and names')
subprocess.run(['git','add','--',*prior],check=True)
need(set(git('diff','--cached','--name-only').splitlines())==set(prior),'exact stage')
csvname=str(csv.relative_to(R))
subprocess.run(['git','diff','--cached','--check','--','.',':(exclude)'+csvname],check=True)
subprocess.run(['git','-c','core.whitespace=cr-at-eol','diff','--cached','--check','--',csvname],check=True)
blobs={n:git('rev-parse',':'+n) for n in prior};need(all(git('hash-object',n)==v for n,v in blobs.items()),'exact blobs')
result=dict(all_passed=True,scope='Separate CSV CRLF-only publication correction; original closure and failed publication retained. Original publication.json was never created and is superseded only by this publication-final.json.',names=names,staged_blobs=blobs,sha256={n:sha(R/n) for n in prior},checks=dict(original_closure=True,original_bindings=True,independent_fix_review=True,exact_nine_CRLF_only=True,default_whitespace_for_all_other_files=True,CSV_cr_at_eol_check=True,exact_complete_names=True,exact_blobs=True))
with (E/'publication-final.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
subprocess.run(['git','add','--',out],check=True)
need(set(git('diff','--cached','--name-only').splitlines())==set(names),'final exact names')
need(all(git('rev-parse',':'+n)==git('hash-object',n) for n in names),'final exact blobs')
print(json.dumps({'all_passed':True,'checks':len(result['checks']),'names':len(names),'listed_blobs':len(blobs)}))
