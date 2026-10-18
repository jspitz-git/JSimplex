"""Task2 exact diagnostic staging; never runs Julia or old checkers."""
from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();E=Path(__file__).resolve().parent
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
def require(ok,message):
 if not ok:raise RuntimeError(message)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((E/'publication-names.json').read_text());names=manifest['names'];closure=json.loads((E/'closure.json').read_text());pub=str((E/'publication.json').relative_to(R));listed=[n for n in names if n!=pub]
require(closure['all_passed'] is True and all(closure['checks'].values()),'closure failed')
require(not git('diff','--cached','--name-only'),'index not empty')
require(len(names)==len(set(names)) and not (E/'publication.json').exists(),'manifest/output not fresh')
for n,h in closure['sha256'].items():require(sha(R/n)==h,'closure binding changed: '+n)
for n in listed:require((R/n).is_file(),'missing '+n)
subprocess.run(['git','add','--',*listed],check=True)
staged=git('diff','--cached','--name-only').splitlines();require(sorted(staged)==sorted(listed),'staged names mismatch')
subprocess.run(['git','diff','--cached','--check'],check=True)
blobs={n:git('rev-parse',':'+n) for n in listed}
for n,h in blobs.items():require(git('hash-object',str(R/n))==h,'staged content mismatch: '+n)
out=dict(all_passed=True,scope='Only offline Task2 adapter/tests/ledger/reviews; no production or Julia',names=names,staged_blobs=blobs,closure_sha256=sha(E/'closure.json'),checks=dict(closure_pass=True,index_initially_empty=True,exact_names=True,all_blobs=True,whitespace=True,output_fresh=True))
with (E/'publication.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
subprocess.run(['git','add','--',pub],check=True)
require(sorted(git('diff','--cached','--name-only').splitlines())==sorted(names),'final exact index mismatch')
subprocess.run(['git','diff','--cached','--check'],check=True)
print(json.dumps(dict(all_passed=True,names=len(names),listed_blobs=len(blobs))))
