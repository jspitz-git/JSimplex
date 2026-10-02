"""Check ordered adaptive events and method-specific productive returns."""
from pathlib import Path
import sys
import tomllib

paths = [Path(x) for x in sys.argv[1:]]
if not paths:
    paths = sorted((Path(__file__).resolve().parents[1] / 'results/intervention-order').glob('*-coordinated.toml'))
assert paths, 'No coordinated reports found'
for path in paths:
    report = tomllib.loads(path.read_text())
    assert not report['original_retry_enabled'], path
    assert not report['weak_pivot_preference'], path
    allowed = {'adaptive_stalling', 'adaptive_pricing', 'adaptive_primal_perturbation',
               'adaptive_dual_perturbation', 'phase_one'}
    assert {k for k, v in report['policy'].items() if v} == allowed, path
    shifts = returns = 0
    for row in report['records']:
        if row['event'] == 'perturbation':
            assert not row.get('temporary', False), (path, 'shift during pricing trial', row)
            shifts += 1
        if row['event'] == 'pricing_progress_return':
            gain = row['monitor_objective_improvement']
            if row['active_algorithm'] == 'dual':
                gain = max(gain, row['monitor_primal_improvement'])
            assert gain > row['monitor_tolerance'], (path, 'secondary-only progress', row)
            returns += 1
    print(path.name, report['status'], 'iterations', report['iterations'],
          'ordered shifts', shifts, 'method-specific returns', returns)
