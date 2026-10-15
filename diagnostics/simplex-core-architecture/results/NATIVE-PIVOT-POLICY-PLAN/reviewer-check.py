"""Independent SOURCE/DESIGN review: read/hash checks only; no historical code execution."""
from pathlib import Path
import hashlib
import json

R = Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
P = R / 'diagnostics/simplex-core-architecture/results/NATIVE-PIVOT-POLICY-PLAN'
def read(p):
    return json.loads(p.read_text())
def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()
def resolved(p):
    p = Path(p)
    return p if p.is_absolute() else R / p
def mismatches(z):
    failures = []
    for n, expected in z['sha256'].items():
        p = resolved(n)
        if not p.is_file() or sha(p) != expected:
            failures.append(n)
    return failures
required = read(P / 'review-required.json')['paths']
source = read(P / 'source-evidence.json')
baseline_path = P.parent / 'DIRECT-LU-PREPARATION/baseline.json'
baseline = read(baseline_path)
entry = read(P / 'entry.json')
host = read(P / 'host.json')
summary = read(P.parent / 'NATIVE-ACCURACY-QUALIFICATION/summary.json')
old_cost_path = P.parent / 'DIRECT-LU-COST-PREPARATION/cost1-audit.json'
checks = {}
details = {}
def check(name, value):
    checks[name] = bool(value)
check('required_39_unique_existing', len(required) == len(set(required)) == 39 and all(Path(p).is_file() for p in required))
source_bad = mismatches(source)
base_bad = mismatches(baseline)
entry_bad = mismatches(entry)
check('source35_all_hashes_match', len(source['sha256']) == 35 and not source_bad)
check('baseline514_all_hashes_match', len(baseline['sha256']) == 514 and not base_bad)
check('entry_all_hashes_match', entry['all_passed'] is True and not entry_bad)
check('source_declared_checks_all_true', source['all_passed'] is True and all(source['checks'].values()))
check('entry_refs_and_old_groups', host['head'] == 'e0c7646c50729eec92f30e754f9718aec4c61382' and host['master'] == '6f68e24e8ddac42b948da8fcc2d636c010751194' and len(host['groups']) == 208 and not host['matches'])
check('baseline_master', baseline['master'] == '6f68e24e8ddac42b948da8fcc2d636c010751194')
check('old_cost1_remains_false', read(old_cost_path)['all_passed'] is False)
check('historical_accuracy_not_recomputed', summary['integrity'] is True and summary['accuracy'] == {'C': False, 'P': True, 'R': True} and summary['per_arm_calls'] == 2126 and summary['failures'] == {'C': 176, 'P': 0, 'R': 0})
check('no_candidate_stage_created', not (P.parent / 'NATIVE-PIVOT-PREPARATION').exists())
loc_fail = []
for name, anchors in source['locations'].items():
    lines = (R / name).read_text().splitlines()
    for needle, line in anchors.items():
        actual = [i + 1 for i, text in enumerate(lines) if needle in text]
        if actual != [line]:
            loc_fail.append([name, needle, line, actual])
check('all_source_anchor_locations', not loc_fail)
f = (R / 'src/factorization.jl').read_text()
o = (R / 'src/options.jl').read_text()
t = (R / 'src/triangular_factorization.jl').read_text()
u_path = Path(required[-1])
u = u_path.read_text()
s = (R / 'docs/superpowers/specs/2026-10-15-native-pivot-policy-design.md').read_text()
p = (R / 'docs/superpowers/plans/2026-10-15-native-pivot-policy.md').read_text()
c = (P / 'continuation-text.md').read_text()
dual_path = R / 'src/dual_simplex.jl'
dual = dual_path.read_text()
check('old_options_16_fields', len([line for line in o.split('struct SolverOptions{T<:Real,M,R}\n', 1)[1].split('\nend', 1)[0].splitlines() if '::' in line]) == 16)
check('old_native_backend_concrete_four_fields', 'mutable struct UMFPACKBackend\n' in f and 'spare::Union{Nothing,Float64UMFPACK}' in f and 'shared::Bool' in f)
check('fresh_native_paths_identified', 'UMFPACKBackend(lu(sparse_basis), rows)' in f and 'candidate = lu(sparse_basis)' in f)
check('copy_active_shared_spare_private', 'backend.shared = true' in f and 'UMFPACKBackend(backend.factorization, backend.dimension, nothing, true)' in f)
check('failed_private_spare_dropped', 'backend.spare = nothing\n            rethrow()' in f)
check('triangular_publish_after_backend', 'new_base = _refactorize_backend(factor.base, B)\n    factor.base = new_base' in t)
check('wrapper_fresh_controls_copied', 'copy(control), Vector{Float64}(undef, UMFPACK_INFO)' in u)
check('wrapper_default_irstep_zero', 'control[JL_UMFPACK_IRSTEP] = 0' in u)
check('wrapper_spare_retains_controls', 'resize!(F.workspace, S, has_refinement(F))' in u and 'return lu!(F; reuse_symbolic, check, q)' in u)
check('wrapper_control_index_imports', 'import ..LibSuiteSparse:' in u and 'const JL_UMFPACK_PIVOT_TOLERANCE = UMFPACK_PIVOT_TOLERANCE + 1' in u)
check('nonfloat_dispatch_unchanged_source', '_factorize_basis(B::AbstractMatrix{T}) where {T<:Real} = _factorize_dense_basis(B)' in f)
check('six_option_paths_in_spec', all(n in s for n in ('_validated_options', 'SolverOptions(T, options)', '_phase_options', '_remaining_options', '_lp_auxiliary_options', '_copy_precision_options')))
check('source_factory_recovery', '_basis_factorization(B,ws.options)' in (R / 'src/simplex_recovery.jl').read_text())
check('source_factory_precision', '_basis_factorization(B,options)' in (R / 'src/simplex_precision.jl').read_text())
check('scope_default_and_no_moi', ':default' in s and ':threshold_one' in s and 'not a new MOI raw' in s)
check('legacy_option_and_backend_compatibility_planned', '16-positional-field' in s and 'two/four-argument UMFPACKBackend' in s)
check('nondefault_hh_markowitz_rejection_planned', 'reject Markowitz and HH' in s and 'Markowitz rejects nondefault before construction' in p)
check('no_hot_loop_policy_or_control_scan_planned', 'No policy lookup belongs in FTRAN/BTRAN/update loops.' in s and 'Do not add repeated 20-control scans' in s)
check('failure_and_roundtrip_tests_planned', 'fail fresh singular construction with no spare' in p and 'fail singular lu! with populated private spare' in p and 'Float64→BigFloat→Float64' in p)
check('cost_component_count_arithmetic', 4 * 2 * (3 + 8) == 88 and 88 * 2 == 176 and 88 * 16 * 3 == 4224 and '88constructions+176refactors+4224solves' in p)
check('separate_admissions_no_runtime_authorization', 'Task1 OFFLINE' in c and 'fresh independent' in p and 'oldcost1FAILED' in c and 'cost2BLOCKED' in c)
check('direct_adapter_deferred', 'separately reviewed new direct-adapter' in s and 'Do not edit the frozen direct source' in p)
check('auxiliary_raw_lu_source_evidence', '_small_dual_refinement_factor(B, ::SolverOptions) = lu(B)' in dual and dual.count('\n        lu(B)\n') == 3)
check('auxiliary_lu_boundary_not_explicit_in_plan', 'small_dual_refinement' not in s + p and 'dual_simplex.jl' not in s + p)
check('actual_work_scope_documentary', 'This document accepts no implementation or runtime behavior.' in s and 'This published step is SOURCE/DESIGN only.' in p)
check('work_and_memory_contract_present', 'One Symbol field per options object and one enum field per native backend' in s and 'does not isolate overhead against the previous binary' in p)
details.update(source_mismatches=source_bad, baseline_mismatches=base_bad, entry_mismatches=entry_bad, source_anchor_mismatches=loc_fail)
extra = [baseline_path, dual_path, R / 'test/basis_recovery_tests.jl', old_cost_path]
result = dict(all_passed=all(checks.values()), check_count=len(checks), checks=checks, required_path_count=len(required), source_hash_count=len(source['sha256']), baseline_hash_count=len(baseline['sha256']), details=details, sha256={n: sha(Path(n)) for n in required}, additional_read_evidence_sha256={str(x): sha(x) for x in extra}, scope='Source/hash verification only. Findings and design acceptance are separate in review.json. No old program or Julia executed; no runtime qualification.')
with (P / 'reviewer-check.json').open('x') as out:
    json.dump(result, out, indent=2)
    out.write('\n')
print(json.dumps({k: result[k] for k in ('all_passed', 'check_count', 'required_path_count', 'source_hash_count', 'baseline_hash_count')}))
if not result['all_passed']:
    print(json.dumps({k: v for k, v in checks.items() if not v}))
    raise SystemExit(1)
