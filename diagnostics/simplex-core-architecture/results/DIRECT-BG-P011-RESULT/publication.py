"""One-shot exact result staging; no numerical or auditor execution."""
from pathlib import Path
import sys,subprocess,json
E=Path(__file__).resolve().parent;D=E.with_name('DIRECT-BG-P011-HARNESS');sys.path.insert(0,str(D));import control as c
R=c.R;names=c.rd(E/'publication-names.json')['names'];target=str((E/'publication.json').relative_to(R))
c.require(names==sorted(set(names)),'Exact sorted names')
c.require(not c.git('diff','--cached','--name-only') and not c.git('diff','--name-only'),'Existing index or tracked edits')
c.require(c.git('rev-parse','HEAD')=='11ebe6bdd401084205ebe628d35539ebb2d5e8ae' and c.git('rev-parse','master')==c.MASTER,'Refs changed')
z=c.rd(E/'closure.json');c.require(z['all_passed'] is True and all(z['checks'].values()) and c.bindings(z),'Closure failed or drift')
actual=c.git('ls-files','--others','--exclude-standard','--',str(D.relative_to(R)),str(E.relative_to(R))).splitlines()
c.require(set(actual)==set(names)-{target},'Exact new file membership')
c.require(all((R/n).is_file() and not (R/n).is_symlink() for n in actual),'Nonregular file')
subprocess.run(['git','add','--',*actual],cwd=R,check=True)
c.require(c.git('diff','--cached','--name-only').splitlines()==sorted(actual),'Exact staging')
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
blobs={n:c.git('hash-object','--',n) for n in actual};hashes={str(R/n):c.sha(R/n) for n in actual}
c.save(E/'publication.json',dict(all_passed=True,checks=dict(closure=True,refs=True,exact_files=True,exact_staging=True,whitespace=True),names=names,blobs_except_self=blobs,sha256=hashes,scope='Self blob verified after write and again in commit, no self-referential hash'))
subprocess.run(['git','add','--',target],cwd=R,check=True)
c.require(c.git('diff','--cached','--name-only').splitlines()==names,'Final staged names')
for n in names:c.require(c.git('rev-parse',':'+n)==c.git('hash-object','--',n),'Staged blob drift')
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
print(json.dumps({'all_passed':True,'exact_staged_files':len(names),'listed_hashes':len(hashes)}))
