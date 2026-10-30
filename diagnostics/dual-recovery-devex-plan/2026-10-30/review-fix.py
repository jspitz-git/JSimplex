from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;W=D.parents[2];bindings={};checks={}
def read(p):
 p=Path(p);b=p.read_bytes();bindings[str(p)]=hashlib.sha256(b).hexdigest();return b.decode()
s=read(W/'docs/superpowers/specs/2026-10-30-dual-recovery-devex-fallback-design.md');p=read(W/'docs/superpowers/plans/2026-10-30-dual-recovery-devex-fallback.md');before=read(D/'plan.before-review.md');bdesign=read(D/'design.before-review.md');src=read(W/'src/simplex_recovery.jl')
checks['old_gate_preserved']='finite retained direction' in before and 'finite-direction scan' in bdesign
checks['original_norm_guard_source']='weight = dot(direction,direction)' in src and 'isfinite(weight) && weight > zero(T) || return false' in src
checks['new_failure_norm_guard']='Before returning fallback_ready, evaluate the existing `dot(direction,direction)`' in p and 'Before marking an inconclusive row eligible, compute the original self-dot' in s
checks['weight_and_refinement_causes_distinct']='reason::_RecoveryWeightReason, refinement_cause::_RefinementCause' in p
checks['no_redundant_scan']='do not add a redundant standalone all(isfinite,direction) scan' in p
checks['ledgers_charge_self_dot']='One self-dot reduction plus original finite-positive scalar guard' in p and 'one self-dot reduction with its finite-positive scalar guard' in s
checks['no_runtime_admission']='PLAN ONLY' in p and '[x]' not in p and 'admits no implementation or numerical launch' in s
if not all(checks.values()):raise RuntimeError(checks)
(D/'review-fix.json').write_text(json.dumps(dict(accepted=True,scope='document correction only',checks=checks,bindings=bindings),indent=2)+'\n');print(json.dumps({'accepted':True,'checks':len(checks),'bindings':len(bindings)}))
