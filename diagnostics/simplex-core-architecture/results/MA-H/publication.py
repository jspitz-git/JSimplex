"""One-shot exact MA-H publication; requires separately completed PASS closure."""
from pathlib import Path
import hashlib,json,subprocess
G=Path(__file__).resolve().parent;R=G.parents[3]
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(v,msg):
 if not v:raise RuntimeError(msg)
names=json.loads((G/'publication-names.json').read_text());selfpath=str((G/'publication.json').relative_to(R));others=[n for n in names if n!=selfpath]
c=json.loads((G/'closure.json').read_text());require(c['all_passed'] and all(c['checks'].values()),'closure')
require(all(sha(R/k)==v for k,v in c['sha256'].items()),'closure hashes')
require(not git('diff','--cached','--name-only'),'index')
actual=set(git('diff','HEAD','--name-only').splitlines())|(set(git('ls-files','--others','--exclude-standard').splitlines())-{'Manifest.toml','LocalPreferences.toml'})
require(actual==set(others),'complete exact names')
subprocess.run(['git','add','--',*others],cwd=R,check=True)
require(set(git('diff','--cached','--name-only').splitlines())==set(others),'staged names')
whitespace=json.loads((G/'whitespace.json').read_text())
check=subprocess.run(['git','diff','--cached','--check'],cwd=R,text=True,capture_output=True)
require(check.returncode in (1,2,3) and check.stdout==whitespace['stdout'] and not check.stderr,'only exact source EOF warning')
require(all(sha(R/k)==v for k,v in whitespace['sha256'].items()),'exact copied whitespace source')
blobs={n:git('rev-parse',':'+n) for n in others}
require(all(git('hash-object',n)==v for n,v in blobs.items()),'staged bytes')
o={'all_passed':True,'checks':{'closure_pass':True,'closure_hashes':True,'exact_complete_names':True,'staged_names':True,'authored_diff_clean_exact_copy_warning_only':True,'staged_blobs':True},'exact_names':names,'sha256':{n:sha(R/n) for n in others},'staged_blobs':blobs,'scope':'Publication self added after creation and verified before commit; exact_names includes itself.'}
with (G/'publication.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
subprocess.run(['git','add','--',selfpath],cwd=R,check=True)
require(set(git('diff','--cached','--name-only').splitlines())==set(names),'final exact names')
require(all(git('rev-parse',':'+n)==git('hash-object',n) for n in names),'final exact staged bytes')
print(json.dumps({'all_passed':True,'exact_names':len(names),'listed_hashes':len(others)}))
