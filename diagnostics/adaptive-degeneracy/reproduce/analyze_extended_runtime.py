"""Compare the extended runtime diagnostic with the preceding 300-second run."""
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
assert long['time_limit'] == 900 and short['time_limit'] == 300
assert long['julia_threads'] == long['blas_threads'] == 1
long_phase = next(r['workspace'] for r in long['records'] if r['event'] == 'phase_one')
short_phase = next(r['workspace'] for r in short['records'] if r['event'] == 'phase_one')
samples = [r for r in long['records'] if r['event'] == 'pivot_completed' and r['workspace'] == long_phase]
previous = {r['iteration']: r for r in short['records'] if r['event'] == 'pivot_completed' and r['workspace'] == short_phase}
compared = []
for row in samples:
    if row['iteration'] not in previous:
        continue
    for key in ('objective', 'pinf', 'pinf_count', 'dinf', 'dinf_count', 'pricing',
                'bound_perturbation_active', 'original_bounds_active', 'bound_level', 'cost_level'):
        assert row.get(key) == previous[row['iteration']].get(key), (row['iteration'], key)
    compared.append(row['iteration'])
final = [r for r in long['records'] if r['event'] == 'final_observed_workspace']
assert len(final) == 1 and final[0]['observation_kind'] == 'uncertified_after_termination'
summary = {
    'scope': 'Sampled pivot events and adaptive transitions, not an optimality or convergence certificate',
    'status': long['status'], 'message': long['message'], 'iterations': long['iterations'],
    'seconds': long['seconds'], 'refactorizations': long['refactorizations'],
    'matching_prior_sample_iterations': compared,
    'sampled_pivots': [{key: r[key] for key in ('iteration', 'seconds', 'objective', 'pinf', 'pinf_count', 'pricing')}
                       for r in samples],
    'events': long['events'],
    'terminal_uncertified': {key: final[0][key] for key in ('iteration', 'objective', 'pinf', 'pinf_count', 'pricing')},
    'phase_events': [{key: r[key] for key in ('event', 'iteration', 'seconds', 'objective')}
                     for r in long['records'] if r['event'].startswith('phase_')],
    'late_transitions': [{key: r[key] for key in ('event', 'iteration', 'seconds', 'objective', 'pinf', 'pricing')}
                         for r in long['records'] if r['iteration'] > max(previous) and
                         r['event'] not in ('pivot_completed', 'final_observed_workspace')],
}
output.write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({k: v for k, v in summary.items() if k not in ('sampled_pivots','late_transitions')}, indent=2))
for row in summary['sampled_pivots']:
    print(row)
