"""Audit completed local validation and retain compact, independently readable evidence."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tomllib

root = Path(__file__).resolve().parents[3]
raw = Path(sys.argv[1]).resolve()
out = root / 'diagnostics/pilotnov-ratio-audit/results'
rows = json.loads((raw / 'validation-results.json').read_text())
expected = {'unscaled', 'targeted', 'semantic', 'pilotnov-matrix', 'external', 'runtime-dual160'}
assert {r['job'] for r in rows} == expected and len(rows) == len(expected)
assert all(r['returncode'] == 0 and r['sources_unchanged'] for r in rows)
assert json.loads((raw / 'validation-current.json').read_text()).get('completed') is True
h = hashlib.sha256()
for p in sorted([root / 'Project.toml', *root.glob('src/**/*.jl')]):
    h.update(str(p.relative_to(root)).encode() + b'\0' + p.read_bytes())
assert all(r['source_sha256'] == h.hexdigest() for r in rows)

def read(name):
    return tomllib.loads((raw / name).read_text())

external = read('external.toml')['cases']
manifest = tomllib.loads((root / 'diagnostics/basis-selective-preparation/reproduce/external-inputs.toml').read_text())['cases']
keys = {(e['id'], alg, backend, manager) for e in manifest
        for alg in ('primal', 'dual') for backend in ('native', 'markowitz')
        for manager in ('pfi', 'huangfu_hall', 'forrest_tomlin', 'suhl_suhl', 'bartels_golub')}
assert len(external) == len(keys) == 100
assert {(e['id'], e['algorithm'], e['backend'], e['basis_update']) for e in external} == keys
refs = {e['id']: e for e in manifest}
for e in external:
    assert e['status'] == 'OPTIMAL' and e['original_primal_certified'] and e['objective_matches']
    assert e['input_sha256'] == refs[e['id']]['sha256']
    assert abs(e['objective'] - refs[e['id']]['objective']) <= max(1e-7, 1e-8 * abs(refs[e['id']]['objective']))
managers = {'pfi', 'huangfu_hall', 'forrest_tomlin', 'suhl_suhl', 'bartels_golub'}
matrix = [tomllib.loads(p.read_text()) for p in sorted((raw / 'matrix').glob('*.toml'))]
assert len(matrix) == 10
assert {(r['manager'], r['backend']) for r in matrix} == {(m,b) for m in managers for b in ('native','markowitz')}
for r in matrix:
    assert r['status'] == 'OPTIMAL' and r['original_primal_feasible'] and r['reference_matches']
    assert r['input_sha256'] == '0885e278d768e76f1819416f7844eeebf39f7c4e965f5c376b75191253d21f8d'
    assert abs(r['objective'] + 4497.2761882188715) < 1e-5
runtime = read('runtime-dual160.toml')
assert runtime['status'] == 'OPTIMAL' and runtime['original_primal_feasible']
assert abs(runtime['objective'] - 51425691.7621) <= 1e-4
files = {'external.toml': 'external.toml', 'runtime-dual160.toml': 'runtime-dual160.toml'}
files.update({r['job'] + '.log': r['job'] + '.log' for r in rows if r['job'] not in ('runtime-dual160', 'semantic')})

for p in (raw/'matrix').glob('*.toml'):
    files[str(p.relative_to(raw))] = 'pilotnov-' + p.name
for src, dest in files.items():
    shutil.copyfile(raw / src, out / dest)
# Preserve the raw semantic log hash below; omit repeated expected warning traces.
semantic_lines = (raw / 'semantic.log').read_text().splitlines()
(out / 'semantic-summary.log').write_text('\n'.join(line for line in semantic_lines
    if line.startswith(('TEST ', 'Test Summary:', 'Native terminal certificate semantic regressions', '\t'))) + '\n')
# Keep phase/final messages and resource totals, not thousands of periodic iteration lines.
lines = (raw / 'runtime-dual160.log').read_text().splitlines()
(out / 'runtime-dual160-summary.log').write_text('\n'.join(
    line for line in lines if not line.startswith('[ Info: iter=')) + '\n')
for r in rows:
    log = raw / (r['job'] + '.log')
    r['log_sha256'] = hashlib.sha256(log.read_bytes()).hexdigest()
    match = re.search(r'Maximum resident set size \(kbytes\): (\d+)', log.read_text())
    r['peak_rss_kib'] = int(match.group(1)) if match else None
    r['wall_seconds'] = r['ended'] - r['started']
validation = dict(source_sha256=h.hexdigest(), external_unique_combinations=100, pilotnov_unique_combinations=10,
                  external_all_original_feasible=True, external_all_reference_matches=True,
                  jobs=rows, files_sha256={str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in sorted([root/'src/dual_simplex.jl', root/'src/solver.jl', root/'test/unscaled_cleanup_tests.jl', root/'test/dual_bfrt_tie_tests.jl', root/'test/dual_breakpoint_queue_tests.jl',
                                   root/'test/dual_simplex_tests.jl', root/'test/runtime_solver_tests.jl', root/'test/runtests.jl', *Path(__file__).parent.glob('*.jl'), *Path(__file__).parent.glob('*.py')]) if p.is_file()})
(out / 'validation.json').write_text(json.dumps(validation, indent=2) + '\n')
print(json.dumps({k: v for k, v in validation.items() if k not in ('jobs', 'files_sha256')}, indent=2))
