"""Narrow report clarification check and diagnostic acceptance recording; no old-check rerun."""
from pathlib import Path
import json,hashlib
K=Path(__file__).resolve().parent;run=K.parent/'NATIVE-PIVOT-INTEGRATION-ENVIRONMENT-AMENDMENT/runs/integration'
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,z):
 with p.open('x') as f:json.dump(z,f,indent=2);f.write('\n')
old=(K/'REPORT.md.before-result-review-clarification').read_text();new=(K/'REPORT.md').read_text()
before='the inclusive60s cap. Those durations include import/compilation/termination and\nare NOT performance measurements. The supplied process identifiers are runner\n'
after='the inclusive60s cap. The inner52.504130901s value is recorded before termination\ncleanup; only the outer56.128167785s duration includes termination. Both include\nstartup/import and any compilation reached; neither is a performance measurement.\nThe supplied process identifiers are runner\n'
initial=rd(K/'result-review-initial.json');checks=rd(K/'result-review-checks.json');audit=rd(run/'audit.json')
c=dict(original_preimage_bound=initial['sha256']=={str(K/'REPORT.md'):sha(K/'REPORT.md.before-result-review-clarification')},exact_single_literal_correction=old.count(before)==1 and new==old.replace(before,after,1),initial_rejection_preserved=initial['accepted'] is False and initial['qualification_accepted'] is False and len(initial['findings'])==1,prior_independent_checks_passed=checks['all_passed'] is True and len(checks['checks'])==34 and all(checks['checks'].values()),original_audit_failure_preserved=audit['all_passed'] is False and audit['error']=="RuntimeError('Exact output membership')" and len(audit['sha256'])==65)
save(K/'result-review-correction-checks.json',dict(all_passed=all(c.values()),checks=c,scope='Narrow literal report correction only; no historical checker or numerical rerun'))
if not all(c.values()):raise RuntimeError('Clarification review failed; preserve all records')
bound=dict(audit['sha256']);bound[str(run/'audit.json')]=sha(run/'audit.json')
assert len(bound)==66 and all(Path(n).is_absolute() for n in bound)
evidence=['result-review-check.py','result-review-checks.json','result-review-correction.py','result-review-correction-checks.json','result-review.md','result-review-initial.json','result-review-initial.md','REPORT.md.before-result-review-clarification','REPORT.md','timeout-postcheck.py','timeout-postcheck.json','timeout-host.json','preflight.json','host.json','admission-review.md','admission-checks.json']
save(K/'result-review.json',dict(accepted=True,qualification_accepted=False,findings=[],scope='diagnostic result',sha256=bound,audit_sha256=sha(run/'audit.json'),evidence_sha256={str(K/n):sha(K/n) for n in evidence},checks=dict(independent_preservation_checks=34,all_passed=True,literal_correction_checks=len(c),initial_reporting_finding_resolved=True),attempt='FAILED/CONSUMED',limits='Diagnostic preservation only. No numerical qualification, partial pass, performance inference, or authorization to repeat the consumed attempt.'))
print(json.dumps(dict(accepted=True,qualification_accepted=False,bindings=len(bound),correction_checks=len(c),evidence=len(evidence))))
