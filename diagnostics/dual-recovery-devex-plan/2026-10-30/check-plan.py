from pathlib import Path
import json,hashlib,re
D=Path(__file__).resolve().parent;W=D.parents[2];spec=W/'docs/superpowers/specs/2026-10-30-dual-recovery-devex-fallback-design.md';plan=W/'docs/superpowers/plans/2026-10-30-dual-recovery-devex-fallback.md';checks={};bindings={}
def read(p):
 p=Path(p);b=p.read_bytes();bindings[str(p)]=hashlib.sha256(b).hexdigest();return b.decode()
s=read(spec);p=read(plan);pins=json.loads(read(D/'source-pins.json'))
for path,sha in pins['bindings'].items():
 if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=sha:raise RuntimeError(path)
checks['four_tasks']=re.findall(r'^### Task (\d):',p,re.M)==['1','2','3','4']
checks['unchecked_runtime_and_implementation']='[x]' not in p and 'PLAN ONLY' in p
checks['reference_spec_exact']=str(spec.relative_to(W)) in p
checks['cause_and_sticky_invalid']='_BasisRefinementOutcome' in p and 'invalid_seen' in p and 'nonfinite cleaned proposal' in p
checks['separate_reason_and_state_roles']='it never prepares or publishes Devex itself' in p and 'Task3 constructor' in p
checks['explicit_algorithm_and_strict_defaults']='algorithm::Symbol=:unspecified' in p and 'only existing external production call site newly opting in' in p
checks['concrete_factor_ownership']='same concrete F type' in p
checks['no_new_callback_emission']='No new observer or logger calls' in s and 'callback-free `_record_recovery!`' in p
checks['fallback_revalidation_budget']='O(N+nnzA)' in p and 'O(N+m+nnzB)' in p
checks['no_private_scratch_fields']='workspace/scratch field layouts' in p and 'persistent per-row metadata' in s
checks['old_failures_not_promoted']='old homogeneous-cleanup failure' in s and 'not a successful steepest-edge qualification' in s
checks['behavioral_RED_not_setup_error']='undefined binding, world-age or environment error is not an accepted RED' in p
checks['ordinary_tests_and_regressions']='ordinary Test' in s and 'dual_weight_validation_tests' in p and 'original primal/optimality certificate' in p
checks['bounded_admission']='four new sequential guarded processes' in p and 'one1800s total ceiling' in p
checks['public_master_separate']='separate production commit/integration and master-verification plan' in p
if not all(checks.values()):raise RuntimeError(checks)
(D/'plan-check.json').write_text(json.dumps(dict(accepted=True,scope='static document consistency only, not executed test or numerical admission',checks=checks,bindings=bindings),indent=2)+'\n');print(json.dumps({'checks':len(checks),'bindings':len(bindings),'accepted':True}))
