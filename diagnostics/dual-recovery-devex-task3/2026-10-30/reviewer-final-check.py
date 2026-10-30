from pathlib import Path
import json,hashlib,subprocess
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-task3/2026-10-30';P=W/'diagnostics/dual-recovery-devex-task2/2026-10-30'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git','-C',str(W),*a],text=True).strip()
initial=json.loads((D/'review-initial.json').read_text());old=json.loads((D/'source-check.json').read_text());fix=json.loads((D/'review-fix.json').read_text())
def initial_path(p):
 if p==str(D/'REPORT.md'):return D/'REPORT.md.before-review'
 return { '/tmp/devex-task3-review.md':D/'REVIEW-INITIAL.md','/tmp/devex-task3-independent-check.py':D/'reviewer-check.py','/tmp/devex-task3-independent-check.json':D/'reviewer-check.json' }.get(p,Path(p))
checks={}
checks['all_94_original_source_bindings_preserved_report_only_remap']=len(old['bindings'])==94 and all(sha(initial_path(p))==h for p,h in old['bindings'].items())
checks['all_98_initial_review_bindings_preserved_exact_copy_remaps']=len(initial['bindings'])==98 and all(sha(initial_path(p))==h for p,h in initial['bindings'].items())
checks['initial_rejection_and_F1_preserved']=not initial['accepted'] and len(initial['findings'])==1 and initial['findings'][0]['id']=='F1'
checks['fix_record_7checks_11bindings']=len(fix['checks'])==7 and all(fix['checks'].values()) and len(fix['bindings'])==11 and all(sha(Path(p))==h for p,h in fix['bindings'].items())
s=(D/'simplex_recovery-reviewed.jl').read_text();original=(D/'simplex_recovery.jl').read_text();anchor='        _recovery_weight_scope(trial,algorithm) || return nothing\n'
checks['sole_production_fix_exact_inverse']=s.count(anchor)==1 and s.replace(anchor,'')==original
build=json.loads((D/'build.json').read_text());inv=s.replace(anchor,'')
for a,b in reversed(build['recovery_changes']):
 assert inv.count(b)==1
 inv=inv.replace(b,a)
checks['full_recovery_inverse_to_task2']=inv==(P/'simplex_recovery.jl').read_text()
checks['numerics_still_identical_task2']=(D/'simplex_numerics.jl').read_bytes()==(P/'simplex_numerics.jl').read_bytes()
a,b=build['pivot_change'];pivot=(D/'simplex_pivot.jl').read_text()
checks['pivot_still_only_actual_algorithm_forwarding']=pivot.count(b)==1 and pivot.replace(b,a)==(W/'src/simplex_pivot.jl').read_text()
fallback=s.split('    if !weights.ok\n',1)[1].split('        return _RecoveryTrialResult(trial,true,weights.failed_row)\n',1)[0]
order=['weights.fallback_ready || return nothing','stop() && return nothing','_recovery_weight_scope(trial,algorithm) || return nothing','_finite_workspace(trial) && _recomputed_basis_reliable(trial) || return nothing','_prepare_recovery_devex!(trial)']
checks['scope_after_exactly_one_stop_before_core_and_reset']=fallback.count('stop()')==1 and all(fallback.index(a)<fallback.index(b) for a,b in zip(order,order[1:]))
t=(D/'recovery_devex_fallback_tests-reviewed.jl').read_text();t0=(D/'recovery_devex_fallback_tests.jl').read_text();ti=t
field='    retained_pricing::Union{Nothing,J.PricingState{Float32},J.PricingState{Float64}}\n';capture='        o.retained_pricing=ws.scratch.pricing\n'
for x in (field,capture):
 assert ti.count(x)==1;ti=ti.replace(x,'')
a='observer=Observe(0,0,(:none,:none,:none),true,:never,:none,failure,nothing)';b='observer=Observe(0,0,(:none,:none,:none),true,:never,:none,failure)';assert ti.count(a)==1;ti=ti.replace(a,b)
start=ti.index('        # F1: an existing callback retained private pricing state');end=ti.index('        for mode in (:nonfinite_core',start);block=ti[start:end];ti=ti[:start]+ti[end:]
checks['test_delta_only_typed_retention_and_window_regression']=ti==t0
checks['window_test_both_neutral_and_mutating_controls']=all(x in block for x in ('for mutate in (false,true)','f.builder.last.corrections==1','held=something(f.observer.retained_pricing)','mutate && (held.algorithm=:primal)','@test post_calls[]==1','@test snapshot(f.ws)==before && f.ws.refactorizations==1','@test f.builder.calls==1 && f.builder.last.corrections==1','@test r===nothing','@test r isa J._RecoveryTrialResult && r.devex_fallback','@test f.ws.progress.diagnostics.counts[:pricing_devex]==0'))
report=(D/'REPORT.md').read_text();before=(D/'REPORT.md.before-review').read_text()
checks['updated_report_append_only_and_canonical_no_runtime_claim']=report.startswith(before) and all(x in report[len(before):] for x in ('simplex_recovery-reviewed.jl','recovery_devex_fallback_tests-reviewed.jl','Neither this test nor any original test has run','Runtime/cost admission remains Task4'))
checks['failed_and_corrected_reviewer_check_copies_preserved']=all(sha(Path('/tmp')/src)==sha(D/dst) for src,dst in [('devex-task3-independent-check-initial.py','reviewer-check-initial.py'),('devex-task3-independent-check-initial.json','reviewer-check-initial.json'),('devex-task3-independent-check.py','reviewer-check.py'),('devex-task3-independent-check.json','reviewer-check.json')])
checks['HEAD_and_master_refs_unchanged']=git('rev-parse','HEAD')=='1509f43f9a288bfa5b3ae004e0e9f07b560b5469' and all(git('rev-parse',r)=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b' for r in ('master','origin/master'))
checks['actual_src_test_unchanged']=not git('diff','HEAD','--','src','test','Project.toml','.github')
bindings={str(initial_path(p)):h for p,h in initial['bindings'].items()};bindings.update(fix['bindings'])
for p in [D/'review-fix.json',D/'reviewer-check-initial.py',D/'reviewer-check-initial.json',Path(__file__)]:bindings[str(p)]=sha(p)
r={'accepted':all(checks.values()),'scope':'Independent bounded F1 source/test review only; no Julia or existing script execution','checks':checks,'bindings':bindings}
Path('/tmp/devex-task3-final-check.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'accepted':r['accepted'],'checks':checks,'bindings':len(bindings)},indent=2))
