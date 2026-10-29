from pathlib import Path
import json,hashlib,subprocess
D=Path(__file__).resolve().parent;W=D.parents[2];prefix=str(D.relative_to(W))+'/'
def git(*args):return subprocess.check_output(['git','-C',str(W),*args],text=True).strip()
def require(v,msg):
 if not v:raise RuntimeError(msg)
closure=json.loads((D/'closure.json').read_text());require(closure['accepted'] and all(closure['checks'].values()),'closure failed')
require(not git('diff','--name-only','HEAD'),'tracked modifications')
require(not git('diff','--cached','--name-only'),'index not empty')
paths=sorted(str(p.relative_to(W)) for p in D.rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts)
require(prefix+'publication.json' not in paths,'fresh publication required')
# Preserved input/vendor whitespace is explicit, byte-bound and never rewritten.
exempt=[]
provenance={}
for rel in exempt[1:]:
 short=rel[len(prefix):];require(hashlib.sha256((W/rel).read_bytes()).hexdigest()==provenance['copied_helpers_identical'][short],'vendor changed')
for rel in paths:
 if rel in exempt:continue
 p=subprocess.run(['git','diff','--no-index','--check','--','/dev/null',str(W/rel)],capture_output=True,text=True)
 require(not p.stdout and not p.stderr and p.returncode in (0,1),'authored whitespace '+rel+' '+p.stdout+p.stderr)
expected_names=sorted(paths+[prefix+'publication.json'])
blobs={rel:git('hash-object',str(W/rel)) for rel in paths}
record=dict(accepted=True,scope='source/analytic assessment only; no production or numerical admission; master unchanged',expected_names=expected_names,blobs_excluding_publication=blobs,verbatim_whitespace_exemptions={rel:hashlib.sha256((W/rel).read_bytes()).hexdigest() for rel in exempt},closure_sha256=hashlib.sha256((D/'closure.json').read_bytes()).hexdigest())
(D/'publication.json').write_text(json.dumps(record,indent=2)+'\n')
# Explicit file arguments, no broad git add or unrelated staging.
subprocess.run(['git','-C',str(W),'add','--',*expected_names],check=True)
actual=git('diff','--cached','--name-only').splitlines();require(actual==expected_names,'staged names mismatch')
all_blobs={rel:git('rev-parse',':'+rel) for rel in actual}
require(all(all_blobs[rel]==git('hash-object',str(W/rel)) for rel in actual),'staged blobs mismatch')
require(all(all_blobs[rel]==blob for rel,blob in blobs.items()),'publication listed blob mismatch')
raw=subprocess.run(['git','-C',str(W),'diff','--cached','--check'],capture_output=True,text=True)
require(not raw.stderr and all(any(line.startswith(rel+':') for rel in exempt) or line.startswith('+') for line in raw.stdout.splitlines()),'unexpected raw whitespace')
seal=dict(accepted=True,names=actual,blobs=all_blobs,raw_whitespace=raw.stdout,publication_blob=all_blobs[prefix+'publication.json'])
sealpath=Path('/tmp/dual-weight-validity-20261030/exact-staged.json');sealpath.write_text(json.dumps(seal,indent=2)+'\n')
print(json.dumps(dict(accepted=True,exact_names=len(actual),exact_staged_blobs=len(all_blobs),listed_blobs=len(blobs),seal=str(sealpath),seal_sha256=hashlib.sha256(sealpath.read_bytes()).hexdigest())))
