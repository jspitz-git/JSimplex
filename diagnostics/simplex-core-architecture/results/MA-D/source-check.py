from pathlib import Path
import json,hashlib,subprocess,tomllib
R=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
e=json.loads((D/'preparation.json').read_text());c=(D/'candidate-markowitz.jl').read_text();helper=(D/'helpers.jl').read_text();inv=json.loads((D/'inverse.json').read_text());src=(R/'src/markowitz_factorization.jl').read_text();t=(D/'candidate-tests-complete.jl').read_text()
checks={'initial_bindings_unchanged':all(h(R/p)==v for p,v in e['sha256'].items()),'whole_source_inverse':c.replace(helper,'').replace(inv['markowitz']['replace_call'],(D/'original-upper-loop.jl').read_text())==src,'canonical_six_named_testsets':all(('MA upper '+x) in t for x in ['dispatch and fallback','scalar ownership','sequential arithmetic','rounding fallback','exceptions','lifecycle']),'canonical_MPFR_flags':'had_range_exception' in t and 'flagged(reference!' in t,'combined_diagonal_faults':'Vector{T}(undef,1)' in t and '=== DivideError' in t,'first_seed_direct':'sub_mul, value, row.values[1]' in helper,'rounding_fallback':'Tuple{Any,Any,Any,Any}' in helper,'nonthrowing_diagonal_guard':'checkbounds(Bool, diagonal, pivot) && isassigned(diagonal, pivot)' in helper,'exact_oracle_checks':json.loads((D/'oracle-checks.json').read_text())['all_passed'],'source_tests_env_CI_unchanged':not subprocess.check_output(['git','diff','HEAD','--','src','test','Project.toml','.github'],cwd=R,text=True),'same_master_production':not subprocess.check_output(['git','diff','master','--','src','test','Project.toml'],cwd=R,text=True)}
paths=[p for p in D.iterdir() if p.is_file()]
paths += [R/'diagnostics/simplex-core-architecture/MA-MARKOWITZ-UPPER-PREPARATION.md',R/'docs/superpowers/plans/2026-10-13-ma-markowitz-upper-admission.md']
paths += [R/p for p in ['src/markowitz_factorization.jl','src/JSimplex.jl','Project.toml','test/runtests.jl','test/markowitz_tests.jl']]
ma=Path('/home/jspitz/.julia/packages/MutableArithmetics/SaQfc')
paths += [ma/p for p in ['Project.toml','src/implementations/BigFloat.jl','src/implementations/BigInt.jl','src/implementations/Rational.jl','src/interface.jl']]
paths += [R/'diagnostics/simplex-core-architecture/MA-MARKOWITZ-UPPER-CONTRACT.md',R/'docs/superpowers/plans/2026-10-13-ma-markowitz-upper-preparation.md']
with (D/'source-check.json').open('x') as f:json.dump({'all_passed':all(checks.values()),'checks':checks,'sha256':{str(p.relative_to(R)) if p.is_relative_to(R) else str(p):h(p) for p in paths},'runtime':'No Julia parse/dispatch/runtime test'},f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'bindings':len(paths)}))
if not all(checks.values()):raise SystemExit(1)
