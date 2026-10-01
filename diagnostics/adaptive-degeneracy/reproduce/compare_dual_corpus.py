#!/usr/bin/env python3
"""Compare paired dual runs; retain failed certificates and bounded outcomes."""
import argparse
import collections
import json
import pathlib
import tomllib

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('base', type=pathlib.Path)
parser.add_argument('candidate', type=pathlib.Path)
parser.add_argument('output', type=pathlib.Path, help='Output prefix for JSON and Markdown')
args = parser.parse_args()
base = tomllib.loads(args.base.read_text())
candidate = tomllib.loads(args.candidate.read_text())
for field in ('julia', 'jump', 'julia_threads', 'blas_threads', 'policy',
              'diagnostic_sha256', 'original_retry_enabled', 'weak_pivot_preference'):
    assert base[field] == candidate[field], (field, base[field], candidate[field])
assert base['julia_threads'] == base['blas_threads'] == 1
assert not base['original_retry_enabled'] and not base['weak_pivot_preference']

def key(row):
    return tuple(row[field] for field in ('id', 'reader', 'algorithm', 'manager', 'seed'))

def records(report):
    rows = {key(row): row for row in report['records']}
    assert len(rows) == len(report['records']), 'Duplicate configuration'
    assert all(row['algorithm'] == 'dual' for row in rows.values())
    return rows

def verified(row):
    certificates = ('original_primal_feasible', 'reader_primal_feasible', 'objective_matches')
    result = row['status'] == 'OPTIMAL' and all(row.get(field, False) for field in certificates)
    assert row['passed'] == result, ('Inconsistent certificate flags', key(row))
    return result

before, after = records(base), records(candidate)
assert before.keys() == after.keys(), 'Different configurations'
fields = ('status', 'iterations', 'refactorizations', 'phases', 'objective')
rows = []
for identity, old in before.items():
    new = after[identity]
    for field in ('input_sha256', 'reference_objective', 'time_limit', 'component_enabled',
                  'rows', 'columns', 'nonzeros', 'exact_model_match', 'rows_reordered', 'columns_reordered'):
        assert old.get(field) == new.get(field), (identity, field)
    assert old.get('exact_model_match') and new.get('exact_model_match'), identity
    rows.append(dict(zip(('id', 'reader', 'algorithm', 'manager', 'seed'), identity),
        before_status=old['status'], after_status=new['status'],
        before_iterations=old.get('iterations'), after_iterations=new.get('iterations'),
        before_verified=verified(old), after_verified=verified(new),
        before_message=old.get('message', old.get('exception', '')),
        after_message=new.get('message', new.get('exception', '')),
        changed_fields=[field for field in fields if old.get(field) != new.get(field)],
        events_changed=old.get('events') != new.get('events'),
        coverage_changed=old.get('coverage') != new.get('coverage')))
summary = {
    'base_production_sha256': base['production_sha256'],
    'candidate_production_sha256': candidate['production_sha256'],
    'configurations': len(rows),
    'base_statuses': dict(collections.Counter(row['before_status'] for row in rows)),
    'candidate_statuses': dict(collections.Counter(row['after_status'] for row in rows)),
    'base_verified': sum(row['before_verified'] for row in rows),
    'candidate_verified': sum(row['after_verified'] for row in rows),
    'unchanged_trajectories': sum(not row['changed_fields'] for row in rows),
    'verification_regressions': sum(row['before_verified'] and not row['after_verified'] for row in rows),
    'base_original_retry_attempts': sum(row['coverage']['original_retry_blocked'] for row in before.values()),
    'candidate_original_retry_attempts': sum(row['coverage']['original_retry_blocked'] for row in after.values()),
    'records': rows,
}
args.output.with_suffix('.json').write_text(json.dumps(summary, indent=2) + '\n')
lines = ['# Paired dual corpus results', '',
         'Status, iteration count, refactorizations, phase sequence and objective are compared exactly.',
         'An optimum is verified only if both primal certificates and the independent objective match pass.',
         'Times include compilation and diagnostics; this is not a speed benchmark.', '',
         '| Model | Reader | Manager | Seed | Before | After | Verified before / after | Changed fields |',
         '| --- | --- | --- | --- | --- | --- | --- | --- |']
for row in rows:
    lines.append('| ' + ' | '.join(str(x) for x in (
        row['id'], row['reader'], row['manager'], row['seed'],
        f"{row['before_status']} / {row['before_iterations']}",
        f"{row['after_status']} / {row['after_iterations']}",
        f"{row['before_verified']} / {row['after_verified']}",
        ', '.join(row['changed_fields']) or 'unchanged')) + ' |')
args.output.with_suffix('.md').write_text('\n'.join(lines) + '\n')
print(json.dumps({key: value for key, value in summary.items() if key != 'records'}, indent=2))
