from pathlib import Path
import sys,json
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');P=W/'diagnostics/dual-recovery-devex-task4/2026-10-30';T=Path('/tmp/dual-recovery-devex-green-fixtures-20261030')
sys.path.insert(0,str(P));import common as C
old=C.read(W/'diagnostics/dual-recovery-devex-task4-green/2026-10-30/postcheck.json')
h=C.host(old['checked_groups'])
C.require(h['refs']['HEAD']=='a2f2415fcc6c9a018ae8209e28f517da1b23b688','unexpected HEAD')
C.require(len(h['checked_groups'])==733,'groups incomplete')
C.require(not C.git('diff','HEAD','--name-only') and not C.git('diff','--cached','--name-only'),'tracked/index dirty')
refs=dict((x.split()[1],x.split()[0]) for x in C.git('ls-remote','origin','refs/heads/master','refs/heads/codex/native-quality-finite').splitlines())
C.require(refs['refs/heads/master']==C.MASTER and refs['refs/heads/codex/native-quality-finite']==h['refs']['HEAD'],'remote mismatch')
identities=[]
for oldid in old['closed_owner_identities']:
 try:now=C.identity(oldid['pid'])
 except (FileNotFoundError,ProcessLookupError):now=None
 C.require(now is None or (now['boot_id'],now['start_ticks'])!=(oldid['boot_id'],oldid['start_ticks']),'old owner present')
 identities.append(dict(original=oldid,current=now))
C.fresh(T/'host.json',dict(accepted=True,scope='offline fixture repair only; no Julia/query/launch',host=h,refs=refs,identities=identities))
print(json.dumps(dict(accepted=True,groups=len(h['checked_groups']),memory=h['memory'],boot=h['boot_id'],head=h['refs']['HEAD'])))
