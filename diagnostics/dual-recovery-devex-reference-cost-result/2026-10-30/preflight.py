from pathlib import Path
import sys,json
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');P=W/'diagnostics/dual-recovery-devex-cost-admission/2026-10-30';T=Path('/tmp/devex-reference-cost-run-20261030')
sys.path.insert(0,str(P));import common as C
phase='reference-cost';h=C.host()
C.require(len(h['checked_groups'])==736 and not h['still_active_current_launcher'],'full736 groups/sessions')
C.require(h['refs']['HEAD']=='d618023b27a42170438c26995c50a036af01c2b4','HEAD changed')
refs=dict((r.split()[1],r.split()[0]) for r in C.git('ls-remote','origin','refs/heads/master','refs/heads/codex/native-quality-finite').splitlines())
C.require(refs['refs/heads/master']==C.MASTER and refs['refs/heads/codex/native-quality-finite']==h['refs']['HEAD'],'remote refs')
used,facts=C.prior(phase);C.require(used==1033.6005972509156 and 1800-used==766.3994027490844,'prior cumulative time')
C.require(not C.RUN.exists(),'cost output/reservation already exists')
C.driver_ready()
old=C.read(C.GREEN2_RESULT/'postcheck.json');identities=[]
for owner in old['closed_owner_identities']:
 try:now=C.identity(owner['pid'])
 except (FileNotFoundError,ProcessLookupError):now=None
 C.require(now is None or (now['boot_id'],now['start_ticks'])!=(owner['boot_id'],owner['start_ticks']),'old owner still present')
 identities.append(dict(original=owner,current=now))
C.fresh(T/'preflight.json',dict(accepted=True,phase=phase,host=h,remote_refs=refs,previous=facts,used_seconds=used,remaining_seconds=1800-used,old_owners=identities,scope='fresh preflight, no numerical launch'))
print(json.dumps(dict(accepted=True,groups=len(h['checked_groups']),boot=h['boot_id'],memory=h['memory'],head=h['refs']['HEAD'],used=used,remaining=1800-used)))
