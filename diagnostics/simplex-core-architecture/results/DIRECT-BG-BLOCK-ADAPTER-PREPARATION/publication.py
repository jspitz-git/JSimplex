"""Exclusive Task2 exact diagnostic staging after successful offline closure."""
from pathlib import Path
import json,hashlib,subprocess
R=Path(__file__).resolve().parents[4];E=Path(__file__).resolve().parent;C=R/'diagnostics/direct-bg-block-upper/reproduce'
W=R/'.superpowers/sdd/2026-10-16-direct-bg-block-upper'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(c,m):
    if not c:raise RuntimeError(m)
def git(*args):return subprocess.check_output(['git',*args],cwd=R).decode().strip()
need(not git('diff','--cached','--name-only'),'Index must start empty')
d=json.loads((E/'closure.json').read_text());need(d['all_passed'] is True and all(d['checks'].values()),'Closure must pass')
need(all(sha(R/k)==h for k,h in d['sha256'].items()),'All closure bindings must match')
files=sorted([p for p in E.iterdir() if p.is_file()]+[C/n for n in d['new_candidate_names']])
expected=set(d['sha256'])|{str((E/'closure.json').relative_to(R))}
need({str(p.relative_to(R)) for p in files}==expected,'Exact closure membership')
need(not (E/'publication.json').exists(),'Publication must be new')
names=sorted(expected|{str((E/'publication.json').relative_to(R))})
need(not git('ls-files','--',*names),'All publication paths must be new')
need(subprocess.run(['git','diff','--quiet','HEAD'],cwd=R).returncode==0,'Original tracked files changed')
out=dict(all_passed=True,scope='Exact Task2 offline diagnostics only; no Julia, actual src/test/env/CI/master or continuation change.',checks=dict(closure_pass=True,all_bindings_match=True,exact_membership=True,index_empty=True,all_new=True,tracked_originals_unchanged=True),names=names,sha256={str(p.relative_to(R)):sha(p) for p in files})
with (E/'publication.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
subprocess.run(['git','add','--',*names],cwd=R,check=True)
need(git('diff','--cached','--name-only').splitlines()==names,'Exact staged names mismatch')
need(all(x.startswith('A\t') for x in git('diff','--cached','--name-status').splitlines()),'Only additions expected')
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
blobs={n:git('rev-parse',':'+n) for n in names}
need(all(hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=R)).hexdigest()==sha(R/n) for n in names),'Staged bytes mismatch')
receipt=dict(parent=git('rev-parse','HEAD'),names=names,blobs=blobs,sha256={n:sha(R/n) for n in names},all_passed=True)
with (W/'task2-staged-receipt.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=True,exact_staged_files=len(names),listed_prepublication_hashes=len(files)),indent=2))
