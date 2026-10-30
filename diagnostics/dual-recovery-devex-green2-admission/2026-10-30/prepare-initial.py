from pathlib import Path
import sys,json,hashlib,subprocess
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');P=W/'diagnostics/dual-recovery-devex-task4/2026-10-30';F=W/'diagnostics/dual-recovery-devex-green-fixture-preparation/2026-10-30';D=W/'diagnostics/dual-recovery-devex-green2-admission/2026-10-30'
sys.path.insert(0,str(P));import common as C
old=C.read(W/'diagnostics/dual-recovery-devex-task4-green/2026-10-30/postcheck.json');h=C.host(old['checked_groups'])
C.require(h['refs']['HEAD']=='514e22c1a5e8a056bb81e4d9a63b1e6003040df1' and len(h['checked_groups'])==733,'refs/groups')
C.require(not C.git('diff','HEAD','--name-only') and not C.git('diff','--cached','--name-only'),'tracked/index')
refs=dict((r.split()[1],r.split()[0]) for r in C.git('ls-remote','origin','refs/heads/master','refs/heads/codex/native-quality-finite').splitlines())
C.require(refs['refs/heads/master']==C.MASTER and refs['refs/heads/codex/native-quality-finite']==h['refs']['HEAD'],'remote refs')
C.require(not D.exists(),'fresh preparation required');D.mkdir(parents=True)
C.fresh(D/'host.json',dict(scope='fresh OFFLINE preparation host; not launch admission',host=h,remote_refs=refs,prior_owners=old['closed_owner_identities']))
copies={}
for src,name in [(P/'guard/guard_reviewed.py','guard/guard_reviewed.py'),(P/'guard/supervisor_reviewed.py','guard/supervisor_reviewed.py'),(P/'guard/entry_gate.py','guard/entry_gate.py'),(F/'fixture_check.py','fixture_check.py'),(F/'fixture-manifest.json','fixture-manifest.json'),(P/'binding_checks.py','binding_checks.py')]:
 dst=D/name;dst.parent.mkdir(parents=True,exist_ok=True)
 with dst.open('xb') as f:f.write(src.read_bytes())
 copies[str(dst)]=dict(source=str(src),sha256=C.sha(src))
pubs=[P,W/'diagnostics/dual-recovery-devex-task4-red/2026-10-30',W/'diagnostics/dual-recovery-devex-task4-green/2026-10-30',F];frozen={}
for p in pubs:
 for name in C.read(p/'publication.json')['expected_names']:frozen[str(W/name)]=C.sha(W/name)
C.fresh(D/'preservation.json',dict(copies=copies,frozen_publications=frozen))
with (D/'prepare.py').open('xb') as f:f.write(Path(__file__).read_bytes())
print(json.dumps(dict(accepted=True,groups=len(h['checked_groups']),memory=h['memory'],frozen_files=len(frozen),copied_helpers=len(copies),scope='offline only, no seal/launch'))))
