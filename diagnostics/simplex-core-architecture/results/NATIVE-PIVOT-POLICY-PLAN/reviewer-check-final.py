"""Fresh final read/hash/source checker. Never executes an earlier checker or Julia."""
from pathlib import Path
import hashlib
import json

R = Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
P = R / 'diagnostics/simplex-core-architecture/results/NATIVE-PIVOT-POLICY-PLAN'
def rd(p):
    return json.loads(p.read_text())
def path(n):
    p = Path(n)
    return p if p.is_absolute() else R / p
def sha(p):
    h = hashlib.sha256()
    with path(p).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()
checks = {}
failures = {}
reconciled = {}
def ck(name, value):
    checks[name] = bool(value)
def bindings(label, record, maps=None):
    maps = maps or {}
    bad = []
    used = []
    for n, h in record['sha256'].items():
        target = path(n)
        if n in maps:
            mapping = maps[n]
            if mapping['sha256'] != h:
                bad.append([n, 'mapping hash differs from original binding'])
                continue
            target = path(mapping['preserved'])
            used.append(dict(original=n, preserved=str(target), sha256=h))
        if not target.is_file() or sha(target) != h:
            bad.append([n, str(target)])
    failures[label] = bad
    reconciled[label] = dict(binding_count=len(record['sha256']), mapped=used)
    ck(label, not bad)
required = rd(P / 'review-final-required.json')['paths']
original_required = rd(P / 'review-required.json')['paths']
source = rd(P / 'source-evidence.json')
initial_review = rd(P / 'review.json')
initial_check = rd(P / 'reviewer-check.json')
fix = rd(P / 'review-fix.json')
link = rd(P / 'review-link-fix.json')
base_path = P.parent / 'DIRECT-LU-PREPARATION/baseline.json'
baseline = rd(base_path)
extra_names = ['continuation.before-final-link.md', 'review-link-fix.py', 'review-link-fix.json']
all_inputs = required + [str(P / n) for n in extra_names]
ck('required51_unique_existing', len(required) == len(set(required)) == 51 and all(Path(n).is_file() for n in required))
ck('original39_in_final_required', len(original_required) == 39 and set(original_required) <= set(required))
ck('three_additional_link_inputs', len(all_inputs) == len(set(all_inputs)) == 54 and all(Path(n).is_file() for n in all_inputs))
expected_maps = {
    str(R / 'docs/superpowers/specs/2026-10-15-native-pivot-policy-design.md'): str(P / 'spec.before-review.md'),
    str(R / 'docs/superpowers/plans/2026-10-15-native-pivot-policy.md'): str(P / 'plan.before-review.md'),
    str(P / 'continuation-text.md'): str(P / 'continuation.before-review.md'),
}
ck('exact_three_original_before_maps', {n: z['preserved'] for n, z in fix['mappings'].items()} == expected_maps)
ck('original_mapping_hashes_match_preserved', all(sha(z['preserved']) == z['sha256'] for z in fix['mappings'].values()))
bindings('source35_mapped', source, fix['mappings'])
bindings('initial_review43_mapped', initial_review, fix['mappings'])
bindings('initial_checker39_mapped', initial_check, fix['mappings'])
ck('original_binding_counts', len(source['sha256']) == 35 and len(initial_review['sha256']) == 43 and len(initial_check['sha256']) == 39)
ck('only_declared_original_mappings_used', len(reconciled['source35_mapped']['mapped']) == 2 and len(reconciled['initial_review43_mapped']['mapped']) == 3 and len(reconciled['initial_checker39_mapped']['mapped']) == 3)
lm = link['mapping']
ck('exact_link_map_record_key', lm['record'] == str(P / 'review-fix.json') and lm['key'] == str(P / 'continuation-text.md') and lm['preserved'] == str(P / 'continuation.before-final-link.md'))
ck('link_map_old_hash', lm['sha256'] == fix['sha256'][lm['key']] == sha(lm['preserved']))
bindings('amendment13_mapped', fix, {lm['key']: lm})
bindings('link4_current', link)
ck('amendment_and_link_record_counts', fix['all_passed'] is True and len(fix['checks']) == 8 and all(fix['checks'].values()) and len(fix['sha256']) == 13 and link['all_passed'] is True and len(link['checks']) == 4 and all(link['checks'].values()) and len(link['sha256']) == 4)
bindings('baseline514_current', baseline)
ck('baseline_count_master', len(baseline['sha256']) == 514 and baseline['master'] == '6f68e24e8ddac42b948da8fcc2d636c010751194')
bindings('entry_current', rd(P / 'entry.json'))
bindings('initial_additional_read_evidence_current', {'sha256': initial_check['additional_read_evidence_sha256']})
ck('initial_rejection_preserved', initial_review['accepted'] is False and [x['id'] for x in initial_review['findings']] == ['F1'])
ck('initial_checker_false_preserved', initial_check['all_passed'] is False and initial_check['check_count'] == 37 and sum(initial_check['checks'].values()) == 36 and [n for n, v in initial_check['checks'].items() if not v] == ['separate_admissions_no_runtime_authorization'])
s = (R / 'docs/superpowers/specs/2026-10-15-native-pivot-policy-design.md').read_text()
p = (R / 'docs/superpowers/plans/2026-10-15-native-pivot-policy.md').read_text()
c = (P / 'continuation-text.md').read_text()
old_c = (P / 'continuation.before-review.md').read_text()
link_c = (P / 'continuation.before-final-link.md').read_text()
a = 'results/NATIVE-PIVOT-POLICY-PLAN/review.md'
b = 'results/NATIVE-PIVOT-POLICY-PLAN/review-final.md'
ck('final_link_exact_inverse', link_c.count(a) == 1 and c.count(b) == 1 and c.replace(b, a) == link_c)
ck('initial_checker_literal_explained', 'oldcost1FAILED' not in old_c and 'Oldcost1FAILED' in old_c and 'cost2BLOCKED' in old_c)
ck('corrected_continuation_stage_boundary', 'Task1 OFFLINE' in c and 'Oldcost1FAILED' in c and 'cost2BLOCKED' in c and 'not a global native-LU override' in c)
ck('spec_managed_scope_explicit', 'It affects managed Float64' in s and 'UMFPACKBackend basis factors constructed through the policy-aware factory' in s and 'threshold-one managed basis factors together with default auxiliary factors' in s)
ck('plan_whole_file_identity_requirement', 'Require whole-file identity of `src/dual_simplex.jl`' in p and 'Policy scope is managed UMFPACKBackend basis factors only' in p)
helpers = ['_try_refine_dual_prices!', '_small_dual_refinement_factor', '_try_refine_dual_direction!', '_try_refine_dual_pivot!']
ck('four_auxiliary_helpers_explicitly_excluded', all(n in s for n in helpers) and 'explicitly outside this option' in s and 'Preserve `src/dual_simplex.jl` byte-for-byte' in s)
dual = (R / 'src/dual_simplex.jl').read_text()
dual_lines = dual.splitlines()
ck('raw_lu_source_lines', all('lu(B)' in dual_lines[n-1] for n in (102,176,949,1012)) and '_small_dual_refinement_factor(B, ::SolverOptions) = lu(B)' in dual)
ck('whole_dual_source_baseline_identity', sha(R / 'src/dual_simplex.jl') == baseline['sha256']['src/dual_simplex.jl'])
r = (R / 'src/simplex_recovery.jl').read_text()
t = (R / 'test/basis_recovery_tests.jl').read_text()
ck('managed_recovery_factory_and_accounting', '_basis_factorization(B,ws.options)' in r and 'ws.refactorizations += 1' in r and 'Fresh managed recovery via `_recovery_trial`' in s)
ck('concrete_recovery_fixture', 'test/basis_recovery_tests.jl' in p and 'Basis checkpoints own working data and preserve consumed work' in p and 'Basis checkpoints own working data and preserve consumed work' in t and 'LinearProblem(sparse([1.0;;]),[1.0];row_lower=[1.0])' in p and '_recovery_trial(w,c,_guard_stop_callback(()->false))' in p and '_guard_stop_callback(stop) = _StopCallback(stop, nothing)' in dual)
ck('cost_native_entry_ledger', '176fresh native LU and88lu! attempts' in p and '88constructions+176refactors+4224solves' in p and 4 * 2 * (3+8) == 88 and 88 * 2 == 176 and 88 * 16 * 3 == 4224)
ck('default_and_precision_contract_retained', 'Default calls the original `lu(B)` path unchanged' in s and 'Float64→BigFloat→Float64' in s and '16-positional-field' in s and 'two/four-argument UMFPACKBackend' in s)
ck('private_ownership_and_no_hot_loop_work_retained', 'Do not add repeated 20-control scans' in s and 'No policy lookup belongs in FTRAN/BTRAN/update loops' in s and 'control vector already belongs to the same immutable backend policy' in s)
ck('all_precision_rejection_and_no_moi_scope_retained', 'reject Markowitz and HH' in s and 'for every scalar type' in s and 'not a new MOI raw' in s)
ck('work_memory_measurement_limits_retained', 'One Symbol field per options object and one enum field per native backend' in s and 'No additional retained native owner' in s and 'does not isolate overhead against the previous binary' in p)
ck('source_design_admission_only', 'This published step is SOURCE/DESIGN only.' in p and 'This document accepts no implementation or runtime behavior.' in s and 'Each numerical stage needs' in p and 'Do not edit the frozen direct source' in p and not (P.parent / 'NATIVE-PIVOT-PREPARATION').exists())
summary = rd(P.parent / 'NATIVE-ACCURACY-QUALIFICATION/summary.json')
ck('historical_false_and_success_counts_retained', summary['accuracy'] == {'C': False, 'P': True, 'R': True} and summary['per_arm_calls'] == 2126 and summary['failures'] == {'C': 176, 'P': 0, 'R': 0})
ck('old_cost1_still_failed', rd(P.parent / 'DIRECT-LU-COST-PREPARATION/cost1-audit.json')['all_passed'] is False)
result = dict(all_passed=all(checks.values()), check_count=len(checks), checks=checks, required_path_count=51, additional_input_count=3, source_hash_count=35, initial_review_binding_count=43, baseline_hash_count=514, reconciled=reconciled, failures=failures, sha256={n:sha(n) for n in all_inputs}, additional_evidence_sha256={str(base_path):sha(base_path)}, scope='Fresh source/hash checks only. No old checker executed, no Julia or numerical work. Initial rejected review and initial false checker retained exactly.')
with (P / 'reviewer-check-final.json').open('x') as f:
    json.dump(result, f, indent=2)
    f.write('\n')
print(json.dumps({k: result[k] for k in ('all_passed','check_count','required_path_count','additional_input_count','source_hash_count','initial_review_binding_count','baseline_hash_count')}))
if not result['all_passed']:
    print(json.dumps({n:v for n,v in checks.items() if not v}))
    raise SystemExit(1)
