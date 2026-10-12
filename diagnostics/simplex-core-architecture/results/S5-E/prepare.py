from pathlib import Path
import hashlib,json,subprocess
r=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=r/'diagnostics/simplex-core-architecture';o=d/'results/S5-E'
def sha(p):return hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
old=json.loads((d/'results/S5-D/evidence.json').read_text())
paths=set(map(Path,old['sha256']))
search=subprocess.check_output(['rg','-l','transfer_precision','test','diagnostics/simplex-core-architecture','--glob','*.jl'],cwd=r,text=True).splitlines()
expected=['test/simplex_precision_tests.jl','test/simplex_precision_state_tests.jl','test/simplex_precision_working_bits_tests.jl','test/huangfu_hall_scalar_integration_tests.jl']
s=(r/'src/simplex_precision.jl').read_text();n=(r/'src/simplex_numerics.jl').read_text();rec=(r/'src/simplex_recovery.jl').read_text();t=(r/'test/simplex_precision_state_tests.jl').read_text();active=t.split('@testset "Precision transfer owns active perturbation journals"')[1].split('@testset')[0];failure=t.split('@testset "Transfer checks invalid bases and shared deadlines"')[1].split('@testset')[0]
checks={
 'prior103_unchanged':len(old['sha256'])==103 and all(sha(p)==h for p,h in old['sha256'].items()),
 'four_scoped_transfer_files':set(search)==set(expected),
 'active_success_without_observer':'observer=' not in active and 'PerturbationJournal(ws)' in active,
 'failure_observer_without_journal':'observer=' in failure and 'PerturbationJournal' not in failure,
 'HH_no_active_journal':'PerturbationJournal' not in (r/expected[3]).read_text(),
 'native_profile_default':'numerical_profile::Symbol=:native' in n,
 'native_refinement_recovery_false':'solve_refinement::Bool=(numerical_profile == :checked)' in n and 'recovery::Bool=(numerical_profile == :checked)' in n,
 'three_refinements':'max_refinements::Integer=3' in n and 'for _ in 1:policy.max_refinements' in rec,
 'reconstruction_refinement_gated':'policy.solve_refinement || return true' in rec,
 'weight_refinement_unconditional':'refine_basis_solve!(direction,trial,rhs,policy,stop;transposed=true).reliable || return false' in rec,
 'value_equality_guard':'journal.active_costs != ws.costs' in s and 'bounds.active_lower == ws.lower && bounds.active_upper == ws.upper' in s,
 'journal_before_recompute':s.index('_copy_precision_journal!(fresh,ws.scratch.perturbations)')<s.index('recompute!(fresh;caller_guard=stop)'),
 'event_before_final_stop':'_simplex_event!(fresh,:refactor_other)\n    stop() && return nothing\n    return fresh' in s,
 'cause_preserved':'caught.cause===callback_failure' in failure,
 'snapshot_dimensions':31*2+26==88 and 76*2+63==215,
 'historical_rows_separate':len([x for x in old['rows'] if x['name'] in ('Precision transfer owns active perturbation journals','Transfer checks invalid bases and shared deadlines')])==4,
}
extra=['src/options.jl','src/simplex_numerics.jl','src/simplex_diagnostics.jl','src/simplex_pricing.jl','src/simplex_start.jl','src/sparse_pricing.jl']+search
paths.update(r/p for p in extra)
paths.update([d/'results/S5-D/evidence.json',d/'results/S5-D/closure.json',d/'S5-PRECISION-JOURNAL-CONTRACT.md',d/'S5-PRECISION-JOURNAL-CONTRACT-REVIEW.md',r/'docs/superpowers/plans/2026-10-13-precision-journal-interruption-preparation.md',o/'host-before.json',o/'prepare.py'])
out=dict(checks=checks,all_passed=all(checks.values()),search_command='rg -l transfer_precision test diagnostics/simplex-core-architecture --glob *.jl',search_hits=search,historical_reuse_rows=[x for x in old['rows'] if x['name'] in ('Precision transfer owns active perturbation journals','Transfer checks invalid bases and shared deadlines')],snapshot_schema={'source_arrays':31,'source_entries':76,'fresh_arrays':26,'fresh_entries':63,'groups_per_case':3,'cases':2,'arrays_per_case':88,'entries_per_case':215},sha256={str(p):sha(p) for p in sorted(paths)})
with (o/'evidence.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'pins':len(paths),'all_passed':out['all_passed']}));assert out['all_passed']
