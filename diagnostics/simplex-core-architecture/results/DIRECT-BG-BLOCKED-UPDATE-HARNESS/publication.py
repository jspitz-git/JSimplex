"""Stage only the fixed explicit package after PASS closure; no commit/push here."""
from control import *
def main():
 names=rd(D/'publication-names.json')['paths'];selfname=str((D/'publication.json').relative_to(R));existing=[n for n in names if n!=selfname]
 require(rd(D/'closure.json')['all_passed'] is True and bindings(rd(D/'closure.json')),'Closure not PASS/current')
 require(not git('diff','--cached','--name-only'),'Index not empty')
 require(all(n.startswith(str(D.relative_to(R))+'/') for n in names),'Publication escaped harness')
 require(set(existing)=={str(p.relative_to(R)) for p in D.rglob('*') if p.is_file()},'Exact package names')
 git('add','--',*existing)
 require(set(git('diff','--cached','--name-only').splitlines())==set(existing),'Exact first staging')
 diff=subprocess.run(['git','diff','--cached','--check'],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 require(diff.returncode==0 and not diff.stdout,'Staged whitespace '+diff.stdout)
 for n in existing:require(git('rev-parse',':'+n)==git('hash-object','--',n),'Staged blob '+n)
 save(D/'publication.json',dict(all_passed=True,staged_names=names,git_blobs={n:git('rev-parse',':'+n) for n in existing},sha256={n:sha(R/n) for n in existing},self_binding='Exact final staging and postcommit self blob check; no recursive selfhash',scope='Only offline diagnostic harness; no Julia or master change'))
 git('add','--',selfname)
 require(set(git('diff','--cached','--name-only').splitlines())==set(names),'Exact final names')
 for n in names:require(git('rev-parse',':'+n)==git('hash-object','--',n),'Final staged blob '+n)
 print('Exact staged names/blobs PASS',len(names))
if __name__=='__main__':main()
