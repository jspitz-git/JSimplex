from pathlib import Path
import hashlib,json,textwrap,re
r=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=r/'diagnostics/simplex-core-architecture';o=d/'results/S5-F'
def sha(p):return hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
e=json.loads((d/'results/S5-E/evidence.json').read_text());s=(o/'driver.jl').read_text();t=(r/'test/simplex_precision_state_tests.jl').read_text()
fixture=t[t.index('        p=LinearProblem'):t.index('        old_checkpoints=')]
expected=textwrap.dedent(fixture)
actual=textwrap.dedent(s.split('    # BEGIN EXISTING FIXTURE (only progress injection differs)\n')[1].split('    # END EXISTING FIXTURE')[0]).replace('JS.','JSimplex.')
actual=actual.replace('SolverOptions(;verbose=false);policy,\n    progress=JSimplex.SimplexProgressContext(p;diagnostics=d,numerical_policy=policy))','SolverOptions(;verbose=false);policy)')
observer=s.split('    observer=(reason,trial)->begin\n')[1].split('    stop=()->begin')[0]
keys=re.findall(r'\(:(\w+),',s.split('    # Exactly 26 arrays')[1].split('        arrays[key]')[0])
checks={
 'prior115_unchanged':len(e['sha256'])==115 and all(sha(p)==h for p,h in e['sha256'].items()),
 'fixture_exact_inverse':actual==expected,
 'two_cases':s.count('for mode in (:stop,:throw)')==1 and s.count('JS.transfer_precision(')==1,
 'three_snapshots':s.count('=snapshot(')==3,
 '26_unique_base_arrays':len(keys)==26 and len(set(keys))==26,
 'snapshot_caps':'checkpoint ? 31 : 26' in s and 'checkpoint ? 76 : 63' in s,
 'no_callback_capture_or_numeric':not any(x in observer for x in ('snapshot(', 'JS.', 'solve','copy(', 'open(')),
 'armed_after_setup':s.index('ws,policy=fixture(d)')<s.index('armed[]=true')<s.index('returned=JS.transfer_precision'),
 'detached_three':all(f'ws.{x}=copy(ws.{x})' in s for x in ('costs','lower','upper')),
 'source_preservation':all(x in s for x in ('isequal(before.arrays,after.arrays)','isequal(before.metadata,after.metadata)')),
 'cause_before_capture':s.index('wrapped_cause=caught isa')<s.index('after=snapshot'),
 'cache_not_created_after_transfer':s.count('JS._sparse_pricing_workspace!')==1,
 'checkpoint_not_revalidated':'_checkpoint_matches' not in s,
 'no_global_methods_or_adapter':not re.search(r'function\s+(?:JS|JSimplex|Base)\.',s) and 'struct ' not in s,
 'pins_before_package_import':s.index('for (path,expected)')<s.index('using JSimplex'),
 'typed_scalar_encoding':'string(Rational{BigInt}(x))' in s and 'bitstring(x)' in s,
 'no_precision_or_tolerance_mutation':'setprecision(' not in s and 'setrounding(' not in s,
 'no_run_output':not (o/'stop.toml').exists() and not (o/'throw.toml').exists(),
}
paths=set(map(Path,e['sha256']));paths.update(r.glob('src/**/*.jl'));paths.update([o/'driver.jl',o/'prepare.py',o/'host-before.json',d/'S5-PRECISION-JOURNAL-INTERRUPTION-PREPARATION.md',d/'S5-PRECISION-JOURNAL-INTERRUPTION-PREPARATION-REVIEW.md',d/'results/S5-E/closure.json',r/'docs/superpowers/plans/2026-10-13-precision-journal-interruption-driver.md'])
# This is a read-time, pre-import manifest, not a future launch inventory.
pins={str(p):sha(p) for p in sorted(paths)}
with (o/'source-pins.toml').open('x') as f:
 f.write('[sha256]\n');f.writelines(json.dumps(p)+' = '+json.dumps(h)+'\n' for p,h in pins.items())
with (o/'evidence.json').open('x') as f:json.dump(dict(checks=checks,all_passed=all(checks.values()),base_array_keys=keys,fixture_source_sha256=hashlib.sha256(expected.encode()).hexdigest(),fixture_inverse_sha256=hashlib.sha256(actual.encode()).hexdigest(),sha256=pins,manifest_sha256=sha(o/'source-pins.toml')),f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'pins':len(pins),'all_passed':all(checks.values())}));assert all(checks.values())
