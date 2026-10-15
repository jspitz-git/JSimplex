"""Preserve failed publication; validate only raw unified-diff context spaces."""
from common import *
import difflib
patch=Q/'candidate.patch';rel=str(patch.relative_to(R))
proc=subprocess.run(['git','diff','--cached','--check'],cwd=R,text=True,capture_output=True)
lines=proc.stdout.splitlines();warn=[]
require(proc.returncode==2 and not proc.stderr,'Unexpected diffcheck result')
require(len(lines)%2==0,'Unexpected warning layout')
raw=patch.read_text().splitlines()
for i in range(0,len(lines),2):
 prefix=rel+':';line=lines[i]
 require(line.startswith(prefix) and line.endswith(': trailing whitespace.'),'Unexpected warning file/type')
 number=int(line[len(prefix):].split(':')[0]);require(raw[number-1]==' ' and lines[i+1]=='+ ','Noncontext whitespace')
 warn.append(number)
inv=rd(Q/'inverse.json');recreated=''
for name in inv['original']:
 src=path(name);dest=Q/'candidate'/src.relative_to(R)
 recreated+=''.join(difflib.unified_diff(src.read_text().splitlines(True),dest.read_text().splitlines(True),fromfile='a/'+str(src.relative_to(R)),tofile='b/'+str(src.relative_to(R))))
checks=dict(exact_diff=recreated==patch.read_text(),context_only=len(warn)==24 and all(raw[i-1]==' ' for i in warn),other_staged_clean=subprocess.run(['git','diff','--cached','--check','--','.',':(exclude)'+rel],cwd=R,capture_output=True).returncode==0,closure_unchanged=rd(Q/'closure.json')['all_passed'] is True and bindings(rd(Q/'closure.json')),final_review_unchanged=rd(Q/'review-final.json')['accepted'] is True and bindings(rd(Q/'review-final.json')),no_publication_output=not (Q/'publication.json').exists())
blobs={n:git('rev-parse',':'+n) for n in git('diff','--cached','--name-only').splitlines()}
save(Q/'publication-failure.json',dict(exit_code=1,git_diff_check_exit=proc.returncode,stdout=proc.stdout,stderr=proc.stderr,staged_blobs=blobs,commit_not_created=git('rev-parse','HEAD')==HEAD,sha256={str(p):sha(p) for p in [Q/'publication.py',Q/'closure.json',patch]},scope='Original publication stopped before commit/push on preserved unified-diff context markers'))
save(Q/'whitespace-supplement.json',dict(all_passed=all(checks.values()),checks=checks,context_lines=warn,sha256={str(p):sha(p) for p in [Path(__file__),patch,Q/'publication-failure.json',Q/'closure.json',Q/'publication.py']},scope='Exactly24single-space context lines in byte-exact unified diff; no candidate or evidence rewrite'))
require(all(checks.values()),'Whitespace supplement failed');print(dict(all_passed=True,checks=len(checks),warnings=len(warn)))
