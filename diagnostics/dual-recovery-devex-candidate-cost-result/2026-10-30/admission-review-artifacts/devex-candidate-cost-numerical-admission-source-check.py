from pathlib import Path
import hashlib,json
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');O=W/'diagnostics/dual-recovery-devex-task4/2026-10-30';P=W/'diagnostics/dual-recovery-devex-cost-admission/2026-10-30';checks={};bindings={}
def text(p):
 b=p.read_bytes();bindings[str(p)]=hashlib.sha256(b).hexdigest();return b.decode()
def check(k,v):
 assert type(v) is bool;checks[k]=v
 if not v:raise AssertionError(k)
r=text(O/'overlays/reference/src/simplex_recovery.jl');c=text(O/'overlays/candidate/src/simplex_recovery.jl');n=text(O/'overlays/candidate/src/simplex_numerics.jl');ref=text(O/'tests/reference.jl').replace('JS.','');driver=text(O/'cost.jl')
rpub=r[r.index('function refine_basis_solve!'):r.index('_checkpoint_model')].strip();fpub=ref[ref.index('function refine_basis_solve!'):ref.index('function _refine_basis_solve!')].strip();check('legacy_public_exact_qualification_only',rpub==fpub)
rkernel=r[r.index('function _refine_basis_solve!'):r.index('# A clock-only guard')].strip();fkernel=ref[ref.index('function _refine_basis_solve!'):].strip().removesuffix('end').strip();check('legacy_kernel_exact_qualification_only',rkernel==fkernel)
original_guard=rpub[rpub.index('    m ='):rpub.index('    if T === BigFloat')];candidate_guard=c[c.index('    m ='):c.index('    if T === BigFloat')];check('normal_alias_dimension_assembly_unchanged',original_guard==candidate_guard)
check('actual_default_api', 'api=side=="reference" ? RefinementReference.refine_basis_solve! : JSimplex.refine_basis_solve!' in driver and 'Val(false);transposed' in c)
check('false_mode_no_outcome', '@inline _refinement_result(::Val{false},quality::SolveQuality,\n                           cause::_RefinementCause,invalid_seen::Bool) = quality' in n and '@inline _refinement_finished(::Val{false},quality::SolveQuality,invalid_seen::Bool) = quality' in n)
check('real_correction_before_declared_zero',driver.index('J.transpose_solve!(x,f.base,rhs)')<driver.index('f.zero_correction && fill!'))
check('original_schedule_and_assertions', 'for k in 1:3' in driver and 'for k in 1:7' in driver and driver.count('GC.gc()')==1 and '@test owners(f)==identity' in driver and '@test f.x==f.initial && f.rhs==savedrhs && f.ws.problem.A==savedB' in driver)
launch=text(P/'launch.py');audit=text(P/'audit.py');common=text(P/'common.py');close=text(P/'close.py');guard=text(P/'guard/guard_reviewed.py');gate=text(P/'guard/entry_gate.py');sup=text(P/'guard/supervisor_reviewed.py')
check('launch_gates_before_attempt',launch.index('C.validate_admission(')<launch.index('C.fresh(r/\'attempt.json\'') and launch.index('C.host()')<launch.index('C.fresh(r/\'attempt.json\''))
check('inclusive_clock_before_attempt',launch.index('started=time.monotonic()')<launch.index('C.fresh(r/\'attempt.json\'') and 'remaining-4' in launch and 'remaining-12' in common)
check('failure_audit_after_caught_supervisor', 'except Exception:C.fresh(r/\'launcher-error.json\'' in launch and launch.index('accepted=audit.main(phase)')>launch.index('elapsed=time.monotonic()-started'))
check('comparison_saved_before_strict_refusal',audit.index("C.fresh(r/'comparison.json',comparison)")<audit.index("C.require(comparison['accepted']"))
check('standalone_full_closure',"set(h['checked_groups'])==C.expected_groups(phase,h['boot_id'],True)" in close and "not h['still_active_current_launcher']" in close)
check('one_process_guard_limits','fcntl.LOCK_EX | fcntl.LOCK_NB' in guard and 'resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))' in guard and 'running = live_julia()' in guard and "6 * 1024**2" in guard and "1024**2" in guard)
check('parent_death_actual_handshake',"sig.value==signal.SIGKILL" in gate and "current['runner']==parent and current['child']==own" in gate and "permit=={'current_sha256':guard.digest(out/'current.json'),'command':command}" in gate and 'os.execvpe(command[0],command,os.environ)' in gate)
check('pidfd_owned_cleanup','os.pidfd_open(identity[\'pid\'],0)' in sup and 'signal.pidfd_send_signal(fd,sig,None,0)' in sup and 'guard.identity_owned' in sup)
text(Path(__file__))
with Path('/tmp/devex-candidate-cost-numerical-admission-source-check-result.json').open('x') as f:json.dump(dict(accepted=True,checks=checks,bindings=bindings),f,indent=2);f.write('\n')
print(json.dumps(dict(accepted=True,checks=len(checks),bindings=len(bindings))))
