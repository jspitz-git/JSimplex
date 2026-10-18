from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();Q=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-U-PREPARATION';N=R/'diagnostics/direct-bg-split-upper/reproduce'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def read(n):return json.loads((Q/n).read_text())
NAMES=['MEMORY-WORK.md', 'REPORT.md', 'author-budget-fix.json', 'author-counter-fix.json', 'geometry-model.json', 'geometry-model.py', 'host-closure.json', 'host.json', 'oracles.before-author-counters.jl.txt', 'original-reserve-renamed.jl.txt', 'prepare.py', 'replacement-reserve.jl.txt', 'review-initial.json', 'review-initial.md', 'review.json', 'review.md', 'reviewer-check-v1.json', 'reviewer-check-v1.py', 'source-check.json', 'source-check.py', 'tests-first.json', 'tests.before-author-budget.jl.txt']
closure=read('closure.json')
if closure['all_passed'] is not True:raise RuntimeError('closure failed')
for n,w in closure['sha256'].items():
 if sha(R/n)!=w:raise RuntimeError('closure hash '+n)
qnames=NAMES+['closure.py','closure.json','publication.py','publication.json']
nnames=['source-bindings.json','split-oracles.jl','split-upper-tests.jl','split-upper.jl']
names=sorted([str((Q/n).relative_to(R)) for n in qnames]+[str((N/n).relative_to(R)) for n in nnames])
out=str((Q/'publication.json').relative_to(R));before=[n for n in names if n!=out]
if sorted(p.name for p in Q.iterdir())!=sorted(n for n in qnames if n!='publication.json'):raise RuntimeError('unexpected Q membership')
if sorted(p.name for p in N.iterdir())!=nnames:raise RuntimeError('unexpected candidate membership')
if git('diff','--name-only') or git('diff','--cached','--name-only'):raise RuntimeError('unexpected tracked/staged changes')
subprocess.run(['git','add','--',*before],check=True)
if git('diff','--cached','--name-only').splitlines()!=before:raise RuntimeError('exact names')
subprocess.run(['git','diff','--cached','--check'],check=True)
blobs={n:git('rev-parse',':'+n) for n in before}
for n,b in blobs.items():
 if git('hash-object','--',n)!=b:raise RuntimeError('blob mismatch '+n)
result={'scope':'Task1 offline publication','all_passed':True,'expected_names':names,'staged_blobs_before_publication':blobs,'publication_self':'Exact publication.json blob checked after exclusive creation and before commit','closure_sha256':sha(Q/'closure.json'),'checks':{'closure_pass':True,'closure_bindings':True,'complete_membership':True,'exact_staged_blobs':True,'diff_check':True},'master_unchanged':'26e2291745999f485a74f643298ca997d65c7205'}
with (Q/'publication.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
subprocess.run(['git','add','--',out],check=True)
if git('diff','--cached','--name-only').splitlines()!=names:raise RuntimeError('final names')
for n in names:
 if git('rev-parse',':'+n)!=git('hash-object','--',n):raise RuntimeError('final blob '+n)
subprocess.run(['git','diff','--cached','--check'],check=True)
print(json.dumps({'all_passed':True,'exact_staged_files':len(names),'recorded_blobs':len(blobs),'publication_blob':git('rev-parse',':'+out)}))
