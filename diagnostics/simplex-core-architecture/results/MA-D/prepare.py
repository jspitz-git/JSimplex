from pathlib import Path
import json,hashlib,tomllib
from fractions import Fraction
R=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent
def save(name,text):
 with (D/name).open('x') as f:f.write(text)
def require(x,msg):
 if not x:raise SystemExit(msg)
source=(R/'src/markowitz_factorization.jl').read_text()
old='''    for pivot in sparse_pivots:-1:1
        value = work[pivot]
        row = backend.upper[pivot]
        for index in eachindex(row.indices)
            value -= row.values[index] * work[row.indices[index]]
        end
        work[pivot] = value / backend.diagonal[pivot]
    end
'''
call='    _markowitz_upper_solve!(work, backend.upper, backend.diagonal, sparse_pivots)\n'
helpers='''# Private scalar scratch exists only during a single upper substitution.
function _markowitz_upper_solve!(work, upper, diagonal, sparse_pivots)
    for pivot in sparse_pivots:-1:1
        value = work[pivot]
        row = upper[pivot]
        for index in eachindex(row.indices)
            value -= row.values[index] * work[row.indices[index]]
        end
        work[pivot] = value / diagonal[pivot]
    end
    return work
end

_markowitz_ma_rounding_matches() =
    Base.MPFR.rounding_raw(BigFloat) == Base.MPFR.ROUNDING_MODE[]

_markowitz_ma_scratch(::Type{T}) where {T} =
    (zero(T), MutableArithmetics.buffer_for(MutableArithmetics.sub_mul, T, T, T))

function _markowitz_ma_row_eligible(seed, row, work, diagonal, pivot)
    length(row.indices) >= 2 && length(row.indices) == length(row.values) || return false
    isfinite(seed) || return false
    checkbounds(Bool, diagonal, pivot) && isassigned(diagonal, pivot) || return false
    isfinite(diagonal[pivot]) || return false
    for i in eachindex(row.indices)
        isassigned(row.values, i) || return false
        source = row.indices[i]
        checkbounds(Bool, work, source) && isassigned(work, source) || return false
        isfinite(row.values[i]) && isfinite(work[source]) || return false
    end
    return true
end

function _markowitz_ma_upper_solve!(work::Vector{T}, upper::Vector{PackedFactorVector{T}},
                                    diagonal::Vector{T}, sparse_pivots::Int) where {T}
    scratch = nothing
    for pivot in sparse_pivots:-1:1
        value = work[pivot]
        row = upper[pivot]
        if _markowitz_ma_row_eligible(value, row, work, diagonal, pivot)
            if isnothing(scratch)
                scratch = _markowitz_ma_scratch(T)
            end
            acc, buffer = scratch
            # First subtraction reads the unrounded, borrowed seed directly.
            MutableArithmetics.buffered_operate_to!(buffer, acc,
                MutableArithmetics.sub_mul, value, row.values[1], work[row.indices[1]])
            for index in 2:length(row.indices)
                MutableArithmetics.buffered_operate!(buffer,
                    MutableArithmetics.sub_mul, acc, row.values[index], work[row.indices[index]])
            end
            value = acc
        else
            for index in eachindex(row.indices)
                value -= row.values[index] * work[row.indices[index]]
            end
        end
        # Ordinary division allocates the independently owned published scalar.
        work[pivot] = value / diagonal[pivot]
    end
    return work
end

function _markowitz_upper_solve!(work::Vector{BigFloat}, upper::Vector{PackedFactorVector{BigFloat}},
                                 diagonal::Vector{BigFloat}, sparse_pivots::Int)
    if !_markowitz_ma_rounding_matches()
        return invoke(_markowitz_upper_solve!, Tuple{Any,Any,Any,Any},
                      work, upper, diagonal, sparse_pivots)
    end
    return _markowitz_ma_upper_solve!(work, upper, diagonal, sparse_pivots)
end

function _markowitz_upper_solve!(work::Vector{Rational{BigInt}},
                                 upper::Vector{PackedFactorVector{Rational{BigInt}}},
                                 diagonal::Vector{Rational{BigInt}}, sparse_pivots::Int)
    return _markowitz_ma_upper_solve!(work, upper, diagonal, sparse_pivots)
end

'''
anchor='function _backend_forward_solve!(destination::Vector{T},\n'
require(source.count(old)==1 and source.count(anchor)==1,'source selectors')
candidate=source.replace(old,call).replace(anchor,helpers+anchor)
require(candidate.replace(helpers,'').replace(call,old)==source,'exact inverse')
save('candidate-markowitz.jl',candidate);save('helpers.jl',helpers);save('original-upper-loop.jl',old)
module=(R/'src/JSimplex.jl').read_text(); candidate_module=module.replace('import OrderedCollections\n','import OrderedCollections\nimport MutableArithmetics\n',1)
require(candidate_module.replace('import MutableArithmetics\n','')==module,'module inverse');save('candidate-JSimplex.jl',candidate_module)
project=(R/'Project.toml').read_text(); cp=project.replace('[deps]\n','[deps]\nMutableArithmetics = "d8a4904e-b15c-11e9-3269-09a3773c0cb0"\n').replace('[compat]\n','[compat]\nMutableArithmetics = "=1.8.1"\n')
parsed=tomllib.loads(cp);require(parsed['compat']['MutableArithmetics']=='=1.8.1','compat');save('candidate-Project.toml',cp)
run=(R/'test/runtests.jl').read_text();cr=run.replace('    include("markowitz_tests.jl")\n','    include("markowitz_tests.jl")\n    include("markowitz_ma_upper_tests.jl")\n',1);require(cr!=run,'test selector');save('candidate-runtests.jl',cr)
# Exact dyadic values have <=8 meaningful bits; every target precision represents them.
fixtures=[]
for n in (8,32):
 for family in ('star','core'):
  a=[[Fraction(0) for j in range(n)] for i in range(n)]
  for i in range(n):
   for j in range(n):
    if family=='core':a[i][j]=Fraction(2 if i==j else 1,1 if i==j else 8)
    elif i==j:a[i][j]=Fraction(2)
    elif i==0:a[i][j]=Fraction(1 if (j+1)%2==0 else -1,8)
  rhs=[sum(row) for row in a]
  for storage in ('sparse','dense'):
   fixtures.append(dict(name=f'{family}{n}_{storage}',n=n,family=family,storage=storage,matrix=[[str(x) for x in row] for row in a],rhs=[str(x) for x in rhs],expected_solution=['1']*n,expected_sparse_pivots=n-2 if family=='star' else 0,expected_upper_terms=n-1 if family=='star' else 0,expected_eligible_rows=1 if family=='star' else 0))
save('fixtures.json',json.dumps({'scalar_cases':['BigFloat128','BigFloat256','BigFloat512','RationalBigInt','Float32','Float64'],'fixtures':fixtures,'scope':'UNEXECUTED prospective constructor and exact endpoint assertions; no runtime pivot capture'},indent=2)+'\n')
inv={'markowitz':{'source':'src/markowitz_factorization.jl','remove_exact':'helpers.jl','replace_call':call,'with':'original-upper-loop.jl'},'module':{'source':'src/JSimplex.jl','remove_exact':'import MutableArithmetics\n'},'project':{'source':'Project.toml','remove_deps_and_compat_key':'MutableArithmetics'},'runtests':{'source':'test/runtests.jl','remove_exact':'    include("markowitz_ma_upper_tests.jl")\n'}}
save('inverse.json',json.dumps(inv,indent=2)+'\n')
checks={'whole_source_inverse':True,'module_inverse':True,'project_direct_dep_and_exact_compat':True,'runtests_one_line':cr.replace('    include("markowitz_ma_upper_tests.jl")\n','')==run,'no_backend_field_added':'mutable struct MarkowitzBackend' not in helpers,'two_exact_specializations':helpers.count('function _markowitz_upper_solve!')==3,'all_fixtures_exact_endpoint':all(all(sum(Fraction(x) for x in row)==Fraction(b) for row,b in zip(f['matrix'],f['rhs'])) for f in fixtures),'48_cost_cases':len(fixtures)*6==48,'upper_selected_source_present':old in source,'original_missing_feature': '_markowitz_ma_scratch' not in source}
paths=['src/markowitz_factorization.jl','src/JSimplex.jl','Project.toml','test/runtests.jl','test/markowitz_tests.jl','diagnostics/simplex-core-architecture/MA-MARKOWITZ-UPPER-CONTRACT.md','docs/superpowers/plans/2026-10-13-ma-markowitz-upper-preparation.md']
paths += [str(p.relative_to(R)) for p in D.iterdir() if p.is_file()]
save('preparation.json',json.dumps({'all_passed':all(checks.values()),'checks':checks,'sha256':{p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in paths},'runtime':'UNEXECUTED, structural missing feature is not Julia RED'},indent=2)+'\n')
require(all(checks.values()),'preparation checks');print(json.dumps(checks))
