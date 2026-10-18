"""Exact new planning-file publication. No commit or push inside this script."""
from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();E=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def need(v,m):
 if not v:raise RuntimeError(m)
names=json.loads((E/'publication-names.json').read_text())['names'];out=str((E/'publication.json').relative_to(R));prior=[n for n in names if n!=out]
c=json.loads((E/'closure.json').read_text());need(c['all_passed'] is True,'closure pass');need(all(sha(R/n)==h for n,h in c['sha256'].items()),'closure bindings')
need(not git('diff','--cached','--name-only'),'index not empty')
need(all(subprocess.run(['git','ls-files','--error-unmatch',n],capture_output=True).returncode!=0 for n in names),'unexpected tracked path')
subprocess.run(['git','add','--',*prior],check=True)
need(set(git('diff','--cached','--name-only').splitlines())==set(prior),'exact stage names')
blobs={n:git('rev-parse',':'+n) for n in prior};need(all(git('hash-object',n)==h for n,h in blobs.items()),'exact blobs')
subprocess.run(['git','diff','--cached','--check'],check=True)
record=dict(all_passed=True,scope='New docs and planning evidence only',names=names,staged_blobs=blobs,closure_sha256=sha(E/'closure.json'),checks=dict(closure_pass=True,closure_bindings=True,new_paths=True,exact_names=True,exact_blobs=True,whitespace=True))
with (E/'publication.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
subprocess.run(['git','add','--',out],check=True);need(set(git('diff','--cached','--name-only').splitlines())==set(names),'final names');need(all(git('hash-object',n)==git('rev-parse',':'+n) for n in names),'final blobs')
print(json.dumps(dict(all_passed=True,names=len(names),listed_blobs=len(blobs))))
