"""One-shot exact publication proof, no commit/push and no numerical calls."""
from pathlib import Path
import sys
E=Path(__file__).resolve().parent;sys.path.insert(0,str(E))
from control_reviewed import *
run=E/'runs'
def main():
 c=rd(E/'closure.json');require(c['all_passed'] and all(c['checks'].values()) and bindings(c),'PASS closure bindings')
 names=sorted(set(c['sha256'])|{str((E/n).relative_to(R)) for n in ['closure.json','publication.json']})
 same=lambda ns:len(ns)==len(set(ns)) and sorted(ns)==names
 require(same(names) and not same(names+['extra']) and not same(names[:-1]) and not same(names+[names[0]]),'Membership negative checks')
 pub=str((E/'publication.json').relative_to(R));files=[n for n in names if n!=pub]
 actual={str(p.relative_to(R)) for base in [E] for p in base.rglob('*') if p.is_file()}
 expected={n for n in files if (R/n).is_relative_to(E) or (R/n).is_relative_to(run)}
 require(actual==expected,'Exact evidence membership')
 require(set(git('diff','--name-only').splitlines())=={'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'} and not git('diff','--cached','--name-only'),'Tracked scope')
 require(git('rev-parse','HEAD')=='0601df628f30ee3f226066d5ace9ab16928193aa' and git('rev-parse','master')==MASTER,'Refs')
 subprocess.run(['git','add','--',*files],cwd=R,check=True);require(git('diff','--cached','--name-only').splitlines()==files,'Exact initial stage names')
 blobs={n:git('rev-parse',':'+n) for n in files};require(all(git('hash-object','--',n)==b for n,b in blobs.items()),'Index blobs')
 raw={n for n in files if (R/n).is_relative_to(run)}|{str((E/n).relative_to(R)) for n in ['STATUS.md.before-COST','roadmap.md.before-COST']}
 ck=subprocess.run(['git','diff','--cached','--check','--',*[n for n in files if n not in raw]],cwd=R,capture_output=True,text=True);require(ck.returncode==0,'Authored whitespace '+ck.stdout+ck.stderr)
 rawcheck=subprocess.run(['git','diff','--cached','--check'],cwd=R,capture_output=True,text=True)
 save(E/'publication.json',dict(all_passed=True,staged_names=names,git_blobs=blobs,sha256={n:sha(R/n) for n in files},raw_diff_check=dict(code=rawcheck.returncode,stdout=rawcheck.stdout,stderr=rawcheck.stderr,verbatim_paths=sorted(raw)),self_binding='Own blob checked externally before failfast commit; exact names include this file'))
 subprocess.run(['git','add','--',pub],cwd=R,check=True)
 require(git('diff','--cached','--name-only').splitlines()==names and all(git('rev-parse',':'+n)==git('hash-object','--',n) for n in names),'Final exact index')
 require(not git('diff','--name-only'),'Unstaged tracked drift');print('Cost preparation publication PASS EXACT',len(names),'names/blobs')
if __name__=='__main__':main()
