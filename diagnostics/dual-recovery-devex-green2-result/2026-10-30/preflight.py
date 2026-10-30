from pathlib import Path
import sys,json
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');P=W/'diagnostics/dual-recovery-devex-green2-admission/2026-10-30';T=Path('/tmp/devex-green2-run-20261030')
sys.path.insert(0,str(P));import common as C
h=C.host();C.require(len(h['checked_groups'])==733 and not h['still_active_current_launcher'],'full prior closure')
C.require(h['refs']['HEAD']=='4f5e6b9966830955637cfb7bba288b9339c9a494','HEAD changed')
refs=dict((a.split()[1],a.split()[0]) for a in C.git('ls-remote','origin','refs/heads/master','refs/heads/codex/native-quality-finite').splitlines())
C.require(refs['refs/heads/master']==C.MASTER and refs['refs/heads/codex/native-quality-finite']==h['refs']['HEAD'],'remote mismatch')
used,facts=C.prior();C.require(used==527.9604928489425 and C.TOTAL-used==1272.0395071510575,'prior budget')
C.require(not C.OUT.exists(),'GREEN2 already sealed/attempted')
fixture=C.fixtures();C.require((fixture['program_count'],fixture['include_edges'],fixture['fixture_count'])==(15,14,2),'fixture graph')
owners=[]
for a in C.read(P/'host.json')['prior_owners']:
 try:now=C.identity(a['pid'])
 except (FileNotFoundError,ProcessLookupError):now=None
 C.require(now is None or (now['boot_id'],now['start_ticks'])!=(a['boot_id'],a['start_ticks']),'old owner present')
 owners.append(dict(original=a,current=now))
C.fresh(T/'preflight.json',dict(accepted=True,host=h,remote_refs=refs,previous=facts,used_seconds=used,remaining_seconds=C.TOTAL-used,fixture_audit=fixture,old_identities=owners,scope='fresh preflight only; no Julia launch'))
print(json.dumps(dict(accepted=True,boot=h['boot_id'],groups=len(h['checked_groups']),memory=h['memory'],head=h['refs']['HEAD'],remaining=C.TOTAL-used,fixtures=fixture['fixture_count'])))
