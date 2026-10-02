"""Compare the observed phase boundary with the prior unchanged-source solve."""
from pathlib import Path
import json
import sys
import tomllib

capture_path, baseline_path, replay_path, output = map(Path, sys.argv[1:])
capture = tomllib.loads(capture_path.read_text())
baseline = tomllib.loads(baseline_path.read_text())
replay = tomllib.loads(replay_path.read_text())
for key in ('input_sha256', 'production_sha256', 'algorithm', 'mode', 'policy',
            'original_retry_enabled', 'weak_pivot_preference', 'diagnostic_method_sha256',
            'phase_failure_method_sha256', 'no_original_retry_method_sha256',
            'time_limit', 'julia_threads', 'blas_threads', 'architecture', 'julia',
            'status', 'message', 'iterations', 'refactorizations', 'events'):
    assert capture[key] == baseline[key], key
assert len(capture['records']) == len(baseline['records'])
ignored = {'seconds', 'workspace', 'monitor'}
for index, (actual, expected) in enumerate(zip(capture['records'], baseline['records'])):
    assert {k: v for k, v in actual.items() if k not in ignored} == {
        k: v for k, v in expected.items() if k not in ignored}, index
assert replay['iteration'] == capture['iterations']
assert replay['auxiliary_optimality_certified']
assert not replay['baseline_transfer_accepted']
summary = {
    'scope': 'Actual phase-boundary capture and local replay; no production modification or Phase-II solve',
    'production_sha256': capture['production_sha256'],
    'matching_trace_records': len(capture['records']),
    'capture_seconds': capture['seconds'],
    'capture_iterations': capture['iterations'],
    'capture_status': capture['status'],
    'artificial_sum': replay['artificial_sum'],
    'nonzero_artificials': replay['nonzero_artificials'],
    'maximum_artificial_magnitude': replay['maximum_artificial_magnitude'],
    'changed_structural_nonbasic_count': sum(row['structural'] for row in replay['changed_nonbasic_values']),
    'changed_nonbasic_count': len(replay['changed_nonbasic_indices']),
    'maximum_nonbasic_change': replay['maximum_nonbasic_change'],
    'complete_export_accepted': replay['complete_export_accepted'],
    'checks': [{k: v for k, v in row.items() if k != 'bounds'} for row in replay['records']],
}
output.write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
