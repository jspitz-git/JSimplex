from pathlib import Path
import sys,json
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');G=W/'diagnostics/dual-recovery-devex-green2-admission/2026-10-30';RESULT=W/'diagnostics/dual-recovery-devex-green2-result/2026-10-30';D=W/'diagnostics/dual-recovery-devex-cost-admission/2026-10-30'
sys.path.insert(0,str(G));import common as C
h=C.host();C.require(len(h['checked_groups'])==736 and not h['still_active_current_launcher'],'full736 closure')
C.require(h['refs']['HEAD']=='6251dafd8be8f94ba4409f560692a893ced7d6a0','HEAD')
C.require(C.read(RESULT/'green2/completion.json')['total_inclusive_seconds']==1033.6005972509156 and C.read(RESULT/'review-final.json')['runtime_accepted'] is True,'GREEN2 result')
refs=dict((x.split()[1],x.split()[0]) for x in C.git('ls-remote','origin','refs/heads/master','refs/heads/codex/native-quality-finite').splitlines())
C.require(refs['refs/heads/master']==C.MASTER and refs['refs/heads/codex/native-quality-finite']==h['refs']['HEAD'],'remote refs')
C.require(not D.exists(),'fresh preparation directory required');D.mkdir(parents=True)
C.fresh(D/'host.json',dict(scope='fresh offline cost preparation; not launch preflight',host=h,remote_refs=refs))
folders=[C.ORIGINAL,C.OLD_RED,C.OLD_GREEN,C.FIX,G,RESULT];frozen={}
for folder in folders:
 for rel in C.read(folder/'publication.json')['expected_names']:frozen[str(W/rel)]=C.sha(W/rel)
copies={}
for name in ('guard/guard_reviewed.py','guard/supervisor_reviewed.py','guard/entry_gate.py','binding_checks.py'):
 src=G/name;dest=D/name;dest.parent.mkdir(parents=True,exist_ok=True)
 with dest.open('xb') as f:f.write(src.read_bytes())
 copies[str(dest)]=dict(source=str(src),sha256=C.sha(src))
C.fresh(D/'preservation.json',dict(copies=copies,frozen_publications=frozen))
with (D/'prepare.py').open('xb') as f:f.write(Path(__file__).read_bytes())
print(json.dumps(dict(accepted=True,groups=len(h['checked_groups']),memory=h['memory'],frozen=len(frozen),copies=len(copies),remaining=1800-1033.6005972509156)))
