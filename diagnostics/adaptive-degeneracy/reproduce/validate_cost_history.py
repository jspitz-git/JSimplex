"""Audit observed cost rebases without treating window values as certificates."""
from collections import Counter
from pathlib import Path
import sys
import tomllib

for arg in sys.argv[1:]:
    path = Path(arg)
    report = tomllib.loads(path.read_text())
    rebases = [r for r in report['records'] if r['event'] == 'stagnation_cost_rebase']
    assert len(rebases) == report['events'].get('stagnation_cost_rebase', 0)
    history = {}
    for row in report['records']:
        if 'monitor' not in row:
            continue
        key = row['monitor']
        if row['event'] in ('perturbation', 'restore_perturbations'):
            history.pop(key, None)
            continue
        values = (row['monitor_observations'], row['monitor_value_scale'], row['monitor_best_primal'])
        if key in history:
            old = history[key]
            assert values[0] >= old[0], (path, 'lost observations', row)
            assert values[1] == old[1], (path, 'incomparable feasibility units', row)
            assert values[2] <= old[2], (path, 'lost feasibility record', row)
        history[key] = values
        if row['event'] == 'stagnation_cost_rebase':
            assert row['active_algorithm'] == 'dual'
            assert row['monitor_objective_improvement'] == 0
            assert row['monitor_dual_improvement'] == 0
    print(path.name, report['status'], 'rebases', len(rebases),
          'rebases per monitor', dict(Counter(r['monitor'] for r in rebases)))
