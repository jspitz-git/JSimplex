#!/usr/bin/env python3
"""Combine the disjoint nine-model and 24-model dual PFI reader runs."""
import argparse
import collections
import hashlib
import json
import pathlib
import tomllib

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('previous', type=pathlib.Path)
parser.add_argument('expanded', type=pathlib.Path)
parser.add_argument('inputs', type=pathlib.Path)
parser.add_argument('output', type=pathlib.Path)
args = parser.parse_args()
previous = tomllib.loads(args.previous.read_text())
expanded = tomllib.loads(args.expanded.read_text())
for field in ('production_sha256', 'diagnostic_sha256', 'policy', 'julia', 'jump',
              'julia_threads', 'blas_threads', 'original_retry_enabled', 'weak_pivot_preference'):
    assert previous[field] == expanded[field], field
inputs = {row['id']: row for row in tomllib.loads(args.inputs.read_text())['cases']}
rows = {}
for source, report in ((str(args.previous), previous), (str(args.expanded), expanded)):
    for row in report['records']:
        if row['reader'] not in ('native', 'jump') or row['manager'] != 'pfi':
            continue
        assert row['algorithm'] == 'dual'
        identity = (row['id'], row['reader'])
        assert identity not in rows, identity
        assert row['input_sha256'] == inputs[row['id']]['sha256']
        certificates = ('original_primal_feasible', 'reader_primal_feasible', 'objective_matches')
        verified = row['status'] == 'OPTIMAL' and all(row.get(key, False) for key in certificates)
        assert row['passed'] == verified, identity
        category = ('verified_optimum' if verified else
                    'uncertified_optimum' if row['status'] == 'OPTIMAL' else
                    'time_limit' if row['status'] == 'TIME_LIMIT' else
                    'numerical_error' if row['status'] == 'NUMERICAL_ERROR' else
                    'presolve_infeasible' if row['status'] == 'INFEASIBLE' and
                        row.get('iterations') == 0 and not row.get('phases') else
                    'other')
        fields = ('id', 'reader', 'status', 'iterations', 'refactorizations', 'message',
                  'passed', 'objective', 'objective_relative_error', 'original_primal_feasible',
                  'reader_primal_feasible', 'objective_matches', 'input_sha256')
        rows[identity] = dict({key: row[key] for key in fields if key in row},
                              category=category, report=source)
assert set(rows) == {(name, reader) for name in inputs for reader in ('native', 'jump')}
summary = {
    'models': len(inputs), 'configurations': len(rows),
    'production_sha256': expanded['production_sha256'],
    'categories': dict(collections.Counter(row['category'] for row in rows.values())),
    'by_reader': {reader: dict(collections.Counter(row['category'] for row in rows.values()
        if row['reader'] == reader)) for reader in ('native', 'jump')},
    'records': list(rows.values()),
}
args.output.with_suffix('.json').write_text(json.dumps(summary, indent=2) + '\n')
lines = ['# Expanded dual PFI verification', '',
         'Nine previously verified models and 24 new models, using identical source and policy hashes.',
         'Only certified original feasible points matching the reference optimum count as verified.', '',
         '| Model | Native dual PFI | JuMP dual PFI |', '| --- | --- | --- |']
for name in inputs:
    cells = [name]
    for reader in ('native', 'jump'):
        row = rows[name, reader]
        cells.append(f"{row['status']} / {row.get('iterations', '?')} ({row['category']})")
    lines.append('| ' + ' | '.join(cells) + ' |')
args.output.with_suffix('.md').write_text('\n'.join(lines) + '\n')
captures = []
for row in expanded['records']:
    for filename in [*row.get('captures', []), *([row['failure_snapshot']] if 'failure_snapshot' in row else [])]:
        path = pathlib.Path(filename)
        entry = {'path': filename, 'id': row['id'], 'reader': row['reader'], 'exists': path.is_file()}
        if path.is_file():
            entry.update(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        else:
            entry['note'] = 'No workspace capture was written; this path is only a harness placeholder.'
        captures.append(entry)
args.output.with_name('captures.json').write_text(json.dumps(captures, indent=2) + '\n')
print(json.dumps({key: value for key, value in summary.items() if key != 'records'}, indent=2))
