"""One-shot exact stage proof, no commit/push. Review and PASS closure required."""
from control import *
def expected_names(c):return sorted(set(c['sha256'])|{str((D/n).relative_to(R)) for n in ('closure.json','publication.json')})
def main():
 c=rd(D/'closure.json');require(c['all_passed'] is True and all(c['checks'].values()),'PASS closure')
 require(bindings(c),'Closure drift');preparation()
 names=expected_names(c);require(len(names)==len(set(names)),'Duplicate paths')
 # Failure sensitivity: extra, missing, duplicate publications are never accepted.
 matches=lambda xs:len(xs)==len(set(xs)) and sorted(xs)==names
 require(matches(names) and not matches(names+['unexpected']) and not matches(names[:-1]) and not matches(names+[names[0]]),'Membership negative checks')
 actual={str(p.relative_to(R)) for p in D.iterdir() if p.is_file()}
 expected={n for n in names if Path(n).parent==D.relative_to(R)}-{str((D/'publication.json').relative_to(R))}
 require(actual==expected,'Unreviewed/missing evidence file')
 S='diagnostics/simplex-core-architecture/STATUS.md';ROAD='docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
 require(set(git('diff','--name-only').splitlines())=={S,ROAD} and not git('diff','--cached','--name-only'),'Tracked/index scope')
 require(git('rev-parse','HEAD')==ENTRY and git('rev-parse','master')==MASTER,'Refs')
 files=[n for n in names if n!=str((D/'publication.json').relative_to(R))]
 subprocess.run(['git','add','--',*files],cwd=R,check=True)
 require(git('diff','--cached','--name-only').splitlines()==sorted(files),'Exact initial index names')
 blobs={n:git('rev-parse',':'+n) for n in files};require(all(git('hash-object','--',n)==b for n,b in blobs.items()),'Index/worktree equality')
 raw={str((D/n).relative_to(R)) for n in ('STATUS.md.before-Task3','roadmap.md.before-Task3')}
 authored=[n for n in files if n not in raw]
 ck=subprocess.run(['git','diff','--cached','--check','--',*authored],cwd=R,text=True,capture_output=True);require(ck.returncode==0,'Authored whitespace '+ck.stdout+ck.stderr)
 allck=subprocess.run(['git','diff','--cached','--check'],cwd=R,text=True,capture_output=True)
 save(D/'publication.json',dict(all_passed=True,staged_names=names,git_blobs=blobs,sha256={n:sha(R/n) for n in files},raw_diff_check=dict(code=allck.returncode,stdout=allck.stdout,stderr=allck.stderr,exact_before_copies=sorted(raw)),self_binding='This record excluded from own hashes; exact index blob verified externally before commit; names include it'))
 subprocess.run(['git','add','--',str(D/'publication.json')],cwd=R,check=True)
 require(git('diff','--cached','--name-only').splitlines()==names,'Final exact names')
 require(all(git('rev-parse',':'+n)==git('hash-object','--',n) for n in names),'Every final index blob')
 require(not git('diff','--name-only'),'Unstaged tracked drift')
 print('Task3 publication PASS EXACT',len(names),'staged names/blobs; ready for failfast commit/push')
if __name__=='__main__':main()
