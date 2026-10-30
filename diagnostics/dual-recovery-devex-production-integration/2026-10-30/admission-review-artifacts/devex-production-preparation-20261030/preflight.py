from pathlib import Path
import sys,json,subprocess
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');P=W/'diagnostics/dual-recovery-devex-cost-admission/2026-10-30';T=Path('/tmp/devex-production-preparation-20261030')
sys.path.insert(0,str(P));import common as C
h=C.host();C.require(len(h['checked_groups'])==742 and not h['still_active_current_launcher'],'full742groups/sessions');C.require(h['refs']['HEAD']=='2d226b84e79e8afeff3ec8d8961b15af44b12085','HEAD changed');C.validate_closed('reference-cost');C.validate_closed('candidate-cost')
g=['git','-c','credential.helper=','-c','credential.https://github.com.helper=!gh auth git-credential','-c','url.https://github.com/.insteadOf=git@github.com:','-C',str(W)]
refs={r.split()[1]:r.split()[0] for r in subprocess.check_output([*g,'ls-remote','origin','refs/heads/master','refs/heads/codex/native-quality-finite'],text=True).splitlines()};C.require(refs=={'refs/heads/master':C.MASTER,'refs/heads/codex/native-quality-finite':h['refs']['HEAD']},'remote refs')
layout={k:C.git('rev-parse',k) for k in ('--git-dir','--git-common-dir','--show-superproject-working-tree')};C.require(layout['--git-dir']!=layout['--git-common-dir'] and not layout['--show-superproject-working-tree'],'existing linked worktree');C.require(C.git('branch','--show-current')=='codex/native-quality-finite','branch')
post=C.read(W/'diagnostics/dual-recovery-devex-candidate-cost-result/2026-10-30/postcheck.json');ids=[]
for owner in post['closed_owner_identities']:
 try:now=C.identity(owner['pid'])
 except (FileNotFoundError,ProcessLookupError):now=None
 C.require(now is None or (now['boot_id'],now['start_ticks'])!=(owner['boot_id'],owner['start_ticks']),'old owner survives');ids.append(dict(original=owner,current=now))
C.fresh(T/'host.json',dict(accepted=True,host=h,remote_refs=refs,worktree=layout,previous_owners=ids,used_seconds=1108.3747013349202,remaining_seconds=691.6252986650798,scope='fresh source-only production preparation; no Julia/launch/new numerical allowance'))
print(json.dumps(dict(accepted=True,groups=len(h['checked_groups']),boot=h['boot_id'],memory=h['memory'],head=h['refs']['HEAD'],master=C.MASTER,existing_isolation=True)))
