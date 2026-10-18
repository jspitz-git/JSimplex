from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd(); Q=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-U-PLAN'
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
closure=json.loads((Q/'closure.json').read_text())
if closure['all_passed'] is not True:raise RuntimeError('closure failed')
for name,want in closure['sha256'].items():
 if sha(R/name)!=want:raise RuntimeError('closure binding '+name)
qnames=['author-check.json','host.json','host-closure.json','spec.before-review.md','plan.before-review.md','review-fix.json','review-initial.md','review-initial.json','reviewer-check-v1.py','reviewer-check-v1.json','reviewer-record-initial.py','reviewer-amendment-v2.py','reviewer-amendment-v2.json','review.md','review.json','reviewer-record-final.py','closure.py','closure.json','publication.py','publication.json']
names=sorted([str(Q.relative_to(R)/n) for n in qnames]+['docs/superpowers/specs/2026-10-18-direct-bg-split-free-blocks.md','docs/superpowers/plans/2026-10-18-direct-bg-split-free-blocks.md'])
out=str((Q/'publication.json').relative_to(R)); before=[n for n in names if n!=out]
if git('diff','--name-only') or git('diff','--cached','--name-only'):raise RuntimeError('unexpected tracked/staged diff')
if sorted(p.name for p in Q.iterdir())!=sorted(n for n in qnames if n!='publication.json'):raise RuntimeError('Q membership')
subprocess.run(['git','add','--',*before],check=True)
if git('diff','--cached','--name-only').splitlines()!=before:raise RuntimeError('staged names')
subprocess.run(['git','diff','--cached','--check'],check=True)
blobs={n:git('rev-parse',':'+n) for n in before}
for n,b in blobs.items():
 if git('hash-object','--',n)!=b:raise RuntimeError('staged blob mismatch '+n)
result={'scope':'exact split free block plan publication','all_passed':True,'expected_names':names,'staged_blobs_before_publication':blobs,'publication_self':'publication.json is staged after exclusive creation; its actual blob is separately checked before commit','closure_sha256':sha(Q/'closure.json'),'checks':{'closure_pass':True,'all_bindings':True,'exact_membership':True,'exact_staged_blobs':True,'diff_check':True},'master_unchanged':'26e2291745999f485a74f643298ca997d65c7205'}
with (Q/'publication.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
subprocess.run(['git','add','--',out],check=True)
if git('diff','--cached','--name-only').splitlines()!=names:raise RuntimeError('final names')
for n in names:
 if git('rev-parse',':'+n)!=git('hash-object','--',n):raise RuntimeError('final blob '+n)
subprocess.run(['git','diff','--cached','--check'],check=True)
print(json.dumps({'all_passed':True,'exact_staged_files':len(names),'recorded_blobs':len(blobs),'publication_blob':git('rev-parse',':'+out)}))
