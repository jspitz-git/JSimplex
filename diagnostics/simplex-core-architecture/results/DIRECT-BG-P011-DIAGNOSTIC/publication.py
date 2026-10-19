"""Exact one-shot staging gate. No numerical execution or source mutation."""
from pathlib import Path
import json,hashlib,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3];prefix=str(D.relative_to(R))+'/'
NAMES=['REPORT.md','REPORT.md.before-review-note','author-check.json','closure.json','closure.py','driver.jl','host-entry.json','progress.md.after-P011','progress.md.before-P011','publication.json','publication.py','review-note-check.json','review.json','review.md','source-bindings.json','source-check.json','source_check.py']
def git(*a):return subprocess.check_output(['git','-C',str(R),*a],text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((D/'closure.json').read_text())
if not c['all_passed'] or not all(sha(D/n)==v for n,v in c['sha256'].items()):raise RuntimeError('Closure binding refusal')
if sorted(p.name for p in D.iterdir())!=sorted(n for n in NAMES if n!='publication.json'):raise RuntimeError('Unexpected/missing files')
if git('diff','--cached','--name-only'):raise RuntimeError('Index not empty')
if git('diff','HEAD','--name-only'):raise RuntimeError('Tracked changes')
blobs={prefix+n:git('hash-object',str(D/n)) for n in NAMES if n!='publication.json'}
result=dict(all_passed=True,names=[prefix+n for n in NAMES],blobs=blobs,scope='Exact17file publication; own blob verified externally before commit')
with (D/'publication.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
expected=dict(blobs);expected[prefix+'publication.json']=git('hash-object',str(D/'publication.json'))
subprocess.run(['git','-C',str(R),'add','--',*[prefix+n for n in NAMES]],check=True)
actual={}
for line in git('ls-files','--stage','--',*[prefix+n for n in NAMES]).splitlines():
 meta,name=line.split('\t');mode,blob,stage=meta.split()
 if stage!='0' or mode!='100644':raise RuntimeError('Unexpected mode/stage')
 actual[name]=blob
if sorted(git('diff','--cached','--name-only').splitlines())!=sorted(expected) or actual!=expected:raise RuntimeError('Exact stage mismatch')
subprocess.run(['git','-C',str(R),'diff','--cached','--check'],check=True)
print(json.dumps(dict(all_passed=True,exact_staged_names=len(expected),exact_staged_blobs=True)))
