"""Exclusive offline text check. Never runs Julia or an older script."""
from pathlib import Path
import hashlib,json,re,subprocess,time
R=Path.cwd();H=Path(__file__).resolve().parent;S=H.parent/'S5-S';P=H.parent/'S5-R'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
p=read(H/'provenance.json');a=(H/'append.jl').read_text();old=(R/'test/simplex_precision_tests.jl').read_bytes();r=(P/'candidate-reviewed.jl').read_text();core=r[r.index('mutable struct S5RProbe'):r.index('    observations=Dict(')]
newcore=a[a.index('mutable struct _BasisInitializationStopProbe'):a.index('    return checks\nend\n\n@testset')]
inverse=newcore
for before,after in p['renames'].items():inverse=inverse.replace(after,before)
callback=newcore[newcore.index('function (probe::'):newcore.index('function _basis_initialization_stop_checks()')]
checks_body=core[core.index('    checks=('):];actual_names=re.findall(r'^    @test checks\.(\w+)$',a,re.M)
red={ 'named_testset_missing':'Supplied-basis checkpoint stop preserves ownership and consumed work' not in old.decode(), 'probe_missing':'_BasisInitializationStopProbe' not in old.decode(), 'guard_identity_predicate_missing':'guard.exception === sentinel' not in old.decode() }
c={
 'actual_prefix_exact':len(old)==7647 and (H/'candidate.jl').read_bytes()==old+a.encode(),
 'preserved_old_test_exact':(H/'original-test.jl').read_bytes()==old and sha(R/'test/simplex_precision_tests.jl')==p['prefix_sha256'],
 'candidate_bound':sha(H/'candidate.jl')==p['candidate_sha256'],
 'append_bound':sha(H/'append.jl')==p['append_sha256'] and len(a.splitlines())==202,
 'literal_core_inverse':inverse==core,
 'core_hash':hashlib.sha256(core.encode()).hexdigest()==p['source_core_sha256'],
 'forty_predicates_unchanged':newcore[newcore.index('    checks=('):]==checks_body,
 'forty_explicit_assertions':actual_names==p['predicate_names'] and len(set(actual_names))==40,
 'one_new_testset':a.count('@testset')==1,
 'one_initializer':a.count('JSimplex.initialize_from_basis(')==1,
 'one_case_call':a.count('checks=_basis_initialization_stop_checks()')==1,
 'no_output_serialization':all(x not in a for x in ('TOML','ARGS','Dict(','observations=','open(output','@assert')),
 'no_callback_array_work':all(x not in callback for x in ('copy(','copyto!','eachindex','solve','recompute!','push!')),
 'no_extra_numerics':all(x not in a for x in ('solve_basis','solve_transposed_basis','recompute!(','solve(p','transfer_solution','make_dual_feasible!')),
 'two_explicit_basis_copies':a.count('copy(')==2,
 'no_new_imports':not re.search(r'^\s*(using|import)\b',a,re.M),
 'helpers_do_not_collide':all(x not in old.decode() for x in p['renames'].values()),
 'structural_RED3_only':all(red.values()),
 'S_audit_and_result_reused':read(S/'audit.json')['all_passed'] is True and len(read(S/'audit.json')['checks'])==19,
 'actual_source_test_environment_CI_unchanged':not subprocess.check_output(['git','diff','master','--','src','test','.github','Project.toml']),
 'all_fresh891_pins_unchanged':len(read(H/'pins.json')['sha256'])==891 and all(sha(k)==v for k,v in read(H/'pins.json')['sha256'].items()),
}
result=dict(checks=c,all_passed=all(c.values()),structural_RED_missing=red,time_ns=time.time_ns(),sha256={str(x):sha(x) for x in [H/'source_check.py',H/'pins.json',H/'provenance.json',H/'candidate.jl',H/'append.jl',H/'entry-checks.json']},scope='Literal offline checks, not Julia parsing, execution, failing runtime RED or CI reproduction.')
with (H/'evidence.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=c,all_passed=result['all_passed'])));raise SystemExit(0 if result['all_passed'] else 1)
