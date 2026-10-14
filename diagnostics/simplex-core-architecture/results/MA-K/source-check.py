from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
PLAN=ROOT/'docs/superpowers/plans/2026-10-14-ma-presolve-selective-routing.md'
SPEC=ROOT/'docs/superpowers/specs/2026-10-14-ma-presolve-selective-routing-design.md'
J=OUT.parent/'MA-J'
BASE=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/base')
MA=Path('/home/jspitz/.julia/packages/MutableArithmetics/SaQfc')
paths=[Path(__file__).resolve(),PLAN,SPEC,OUT/'host.json',OUT/'STATUS.md.before-MA-K',OUT/'roadmap.md.before-MA-K',ROOT/'src/presolve_aggregation.jl',ROOT/'src/presolve_rows.jl',ROOT/'src/model.jl',ROOT/'Project.toml',J/'candidate.jl',J/'reference.jl',J/'result-review.md',J/'result-review.json',J/'run-2/raw.toml',ROOT/'diagnostics/simplex-core-architecture/MA-PRESOLVE-EQUALITY-QUALIFICATION.md',BASE/'gmp.jl',BASE/'intfuncs.jl',MA/'Project.toml',MA/'src/implementations/Rational.jl',MA/'src/implementations/BigInt.jl']
p=PLAN.read_text(); s=SPEC.read_text(); source=(ROOT/'src/presolve_aggregation.jl').read_text(); rows=(ROOT/'src/presolve_rows.jl').read_text()
checks={
'caller_length_cap':'2 <= length(terms) <= 8' in source,
'caller_fill_cap':'fill_estimate <= 10' in source,
'caller_total_cap':'estimated_updates + fill_estimate <= 200_000' in source,
'ordinary_row_type':'Vector{Tuple{Int,T}}' in rows,
'generic_signature':'problem::LinearProblem, row_terms,' in source,
'original_shared_denominator':'Rational{BigInt}(numerator(other_min) + numerator(product), denominator(other_min))' in source,
'base2_bigint_route':'MPZ.sizeinbase(x, b)' in (BASE/'gmp.jl').read_text(),
'public_ndigits_route':'ndigits(x::Integer; base::Integer=10, pad::Integer=1)' in (BASE/'intfuncs.jl').read_text(),
'grid_count':24+12+9+4+27==76,
'window_schedule':76*2*(3+7)==1520 and 1520*128*3==583680,
'fixed_selection':'bit lengths>=129' in p and 'position<=3' in p,
'ownership_rule':'ALL nonzero additions after activation' in p,
'control_rejection':'For EACH control require pooled median ratio<=1.00' in p,
'plan_only':'Planning/review only in MA-K' in p,
'no_current_candidate':not (OUT/'candidate.jl').exists(),
'future_fullpass_gate':'whole-pass cost' in p,
}
sha={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in paths}
data={'all_passed':all(checks.values()),'checks':checks,'sha256':sha,'scope':'New offline source/planning checks only. Read-time hashes, not historical launch pins. No Julia or numerical experiment.'}
with (OUT/'source-check.json').open('x') as f: json.dump(data,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':data['all_passed'],'checks':checks,'hash_count':len(sha)}))
if not data['all_passed']: raise SystemExit(1)
