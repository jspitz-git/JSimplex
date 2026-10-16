"""Post-commit exact blob/remote verification; no mutation or numerical work."""
from common import *
v=rd(Q/'publication.json');names=v['staged_names'];head=git('rev-parse','HEAD')
require(v['all_passed'] is True,'Publication failure')
require(set(git('diff-tree','--no-commit-id','--name-only','-r',head).splitlines())==set(names),'Committed membership')
for n in names:
 require(subprocess.check_output(['git','show',head+':'+n],cwd=R)==(R/n).read_bytes(),'Committed bytes '+n)
 if n in v['other_blobs']:require(git('rev-parse',head+':'+n)==v['other_blobs'][n],'Committed blob '+n)
require(git('rev-parse','master')==MASTER,'Master changed')
remote=dict((b,a) for a,b in (line.split() for line in git('ls-remote','origin','refs/heads/codex/simplex-core-architecture','refs/heads/master').splitlines()))
require(remote['refs/heads/codex/simplex-core-architecture']==head and remote['refs/heads/master']==MASTER,'Remote mismatch')
require(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'Tracked/index changes')
print(dict(commit=head,names=len(names),other_blobs=len(v['other_blobs']),master=MASTER,remote_verified=True,tracked_clean=True))
