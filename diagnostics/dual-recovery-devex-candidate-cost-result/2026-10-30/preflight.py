from pathlib import Path
import sys,json
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');P=W/'diagnostics/dual-recovery-devex-cost-admission/2026-10-30';T=Path('/tmp/devex-candidate-cost-run-20261030')
sys.path.insert(0,str(P));import common as C
phase='candidate-cost';h=C.host();C.require(len(h['checked_groups'])==739 and not h['still_active_current_launcher'],'full739 groups/sessions');C.require(h['refs']['HEAD']=='14720147d8850525c0603921064dfe3ba83d3fcb','HEAD changed')
refs={r.split()[1]:r.split()[0] for r in C.git('ls-remote','origin','refs/heads/master','refs/heads/codex/native-quality-finite').splitlines()};C.require(refs['refs/heads/master']==C.MASTER and refs['refs/heads/codex/native-quality-finite']==h['refs']['HEAD'],'remote refs')
used,facts=C.prior(phase);C.require(used==1070.9948121299385 and 1800-used==729.0051878700615,'prior cumulative time');C.require(not C.out(phase).exists(),'candidate output/reservation exists');C.driver_ready()
prior=C.read(W/'diagnostics/dual-recovery-devex-reference-cost-result/2026-10-30/postcheck.json');identities=[]
for owner in prior['closed_owner_identities']:
 try:now=C.identity(owner['pid'])
 except (FileNotFoundError,ProcessLookupError):now=None
 C.require(now is None or (now['boot_id'],now['start_ticks'])!=(owner['boot_id'],owner['start_ticks']),'old owner still present');identities.append(dict(original=owner,current=now))
review=C.read(W/'diagnostics/dual-recovery-devex-reference-cost-result/2026-10-30/review-final.json');C.require(review['accepted'] is True and review['runtime_accepted'] is True and review['cost_qualified'] is False and all(C.sha(n)==v for n,v in review['bindings'].items()),'reference independent result review')
C.fresh(T/'preflight.json',dict(accepted=True,phase=phase,host=h,remote_refs=refs,previous=facts,used_seconds=used,remaining_seconds=1800-used,old_owners=identities,reference_review_sha256=C.sha(W/'diagnostics/dual-recovery-devex-reference-cost-result/2026-10-30/review-final.json'),scope='fresh candidate preflight; no numerical launch'))
print(json.dumps(dict(accepted=True,groups=len(h['checked_groups']),boot=h['boot_id'],memory=h['memory'],head=h['refs']['HEAD'],used=used,remaining=1800-used)))
