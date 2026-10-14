"""Fixed-name failfast diagnostic staging/publication; never stages user files."""
from pathlib import Path
import subprocess,json,hashlib
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-J'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(x,m):
 if not x:raise ValueError(m)
def git(*args):return subprocess.check_output(['git',*args])
names=read(D/'publication-names.json');pub=str((D/'publication.json').relative_to(R));closure=read(D/'closure.json')
require(closure['all_passed'] is True and all(closure['checks'].values()),'closure not accepted')
require(all(sha(p)==v for p,v in closure['sha256'].items()),'closure binding changed')
require(not git('diff','--cached','--name-only').strip(),'index not empty')
require(not (D/'publication.json').exists(),'publication exists')
others=[n for n in names if n!=pub]
# Stage only the exact explicit names, including diagnostic environment copies.
subprocess.run(['git','add','-f','--pathspec-from-file=-','--pathspec-file-nul'],input=b'\0'.join(n.encode() for n in others)+b'\0',check=True)
actual=git('diff','--cached','--name-only','-z').decode().split('\0')[:-1]
require(sorted(actual)==sorted(others),'unexpected staging')
subprocess.run(['git','diff','--cached','--check'],check=True)
blobs={n:git('rev-parse',':'+n).decode().strip() for n in others}
require(all(blobs[n]==git('hash-object',n).decode().strip() for n in others),'staged contents differ')
record=dict(all_passed=True,checks=dict(closure_pass=True,closure_bindings=True,exact_staged_names=True,exact_staged_blobs=True,whitespace_clean=True),exact_names=names,sha256={n:sha(R/n) for n in others},staged_blobs=blobs,scope='Exact full names include publication itself; self-hash excluded; verified complete index below before any commit')
with (D/'publication.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
subprocess.run(['git','add','-f','--',pub],check=True)
require(sorted(git('diff','--cached','--name-only','-z').decode().split('\0')[:-1])==sorted(names),'complete index mismatch')
require(all(git('rev-parse',':'+n).strip()==git('hash-object',n).strip() for n in names),'complete blobs mismatch')
subprocess.run(['git','diff','--cached','--check'],check=True)
print(json.dumps(dict(all_passed=True,exact_names_count=len(names),full_staged_blobs={n:git('rev-parse',':'+n).decode().strip() for n in names}),indent=2))
