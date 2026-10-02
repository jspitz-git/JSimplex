"""Compare the longer runtime solve with its 900-second production baseline."""
from pathlib import Path
import json
import sys
import tomllib

long_path, short_path, output = map(Path, sys.argv[1:])
long = tomllib.loads(long_path.read_text())
short = tomllib.loads(short_path.read_text())
for key in ('input_sha256', 'production_sha256', 'algorithm', 'mode', 'policy',
            'original_retry_enabled', 'weak_pivot_preference', 'diagnostic_method_sha256',
            'phase_failure_method_sha256', 'no_original_retry_method_sha256'):
    assert long[key] == short[key], key
assert long['time_limit'] == 1800 and short['time_limit'] == 900
assert long['julia_threads'] == long['blas_threads'] == 1
keys = ('event', 'iteration', 'iteration_offset', 'total_iterations', 'objective',
        'pinf', 'pinf_count', 'dinf', 'dinf_count', 'pricing', 'active_algorithm',
        'rows', 'columns', 'bound_perturbation_active', 'original_bounds_active',
        'bound_level', 'cost_level', 'temporary', 'return_mode', 'transition',
        'observations', 'trial_until')
prior = [r for r in short['records'] if r['event'] != 'final_observed_workspace']
assert len(long['records']) >= len(prior)
for index, (before, after) in enumerate(zip(prior, long['records'])):
    for key in keys:
        assert before.get(key) == after.get(key), (index, before['iteration'], key)
phase_id = next(r['workspace'] for r in long['records'] if r['event'] == 'phase_one')
samples = [r for r in long['records'] if r['event'] == 'pivot_completed' and r['workspace'] == phase_id]
final = [r for r in long['records'] if r['event'] == 'final_observed_workspace']
assert len(final) == 1 and final[0]['observation_kind'] == 'uncertified_after_termination'
phase_events = [r for r in long['records'] if r['event'].startswith('phase_')]
summary = {
    'scope': 'Sampled events; only an OPTIMAL returned result can certify completion',
    'status': long['status'], 'message': long['message'], 'iterations': long['iterations'],
    'seconds': long['seconds'], 'refactorizations': long['refactorizations'],
    'matching_prior_event_count': len(prior),
    'matching_prior_pivot_sample_count': sum(r['event'] == 'pivot_completed' for r in prior),
    'phase_one_sampled_pivots': [{key: r[key] for key in ('iteration', 'seconds', 'objective', 'pinf', 'pinf_count', 'pricing')}
                               for r in samples],
    'events': long['events'],
    'terminal_uncertified': {key: final[0][key] for key in ('iteration', 'total_iterations', 'objective', 'pinf', 'pinf_count', 'pricing')},
    'phase_events': [{key: r[key] for key in ('event', 'iteration', 'total_iterations', 'seconds', 'objective', 'rows', 'columns')}
                     for r in phase_events],
    'late_transitions': [{key: r[key] for key in ('event', 'iteration', 'total_iterations', 'seconds', 'objective', 'pinf', 'pricing')}
                         for r in long['records'][len(prior):]
                         if r['event'] not in ('pivot_completed', 'final_observed_workspace')],
}
if long['status'] == 'OPTIMAL':
    assert long['original_primal_feasible']
    reference = 51425691.762103125
    summary['objective'] = long['objective']
    summary['original_primal_feasible'] = True
    summary['prior_dual_reference_objective'] = reference
    summary['objective_difference_from_prior_dual'] = long['objective'] - reference
output.write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({k: v for k, v in summary.items() if k not in ('phase_one_sampled_pivots', 'late_transitions')}, indent=2))
