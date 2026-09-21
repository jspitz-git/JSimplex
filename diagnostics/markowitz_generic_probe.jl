using JSimplex, SparseArrays, LinearAlgebra, Test, TOML
BLAS.set_num_threads(1)
include(joinpath(pwd(), "dev", "allocations.jl"))
using .JSimplexAllocations: measure_allocations

baseline_source = read("/tmp/jsimplex-markowitz-after-csc.jl", String)
baseline_magnitude = """
_pivot_magnitude(value::Real) = abs(value)
_pivot_magnitude(value::BigFloat) = setprecision(BigFloat, precision(value)) do
    abs(value)
end
"""
fast_magnitude = """
_pivot_magnitude(value::Real) = abs(value)
function _pivot_magnitude(value::BigFloat)
    signbit(value) || return value
    result = BigFloat(precision=precision(value))
    ccall((:mpfr_neg, Base.MPFR.libmpfr), Cint,
          (Ref{BigFloat}, Ref{BigFloat}, Base.MPFR.MPFRRoundingMode),
          result, value, Base.MPFR.MPFRRoundNearest)
    return result
end
"""
function source_variant(; zeros=false, magnitude=false, rational=false, rational_cache=false)
    source = baseline_source
    if zeros
        source = replace(source, "    rows = [Dict{Int,T}() for _ in 1:n]" => "    entry_zero = zero(T)\n    rows = [Dict{Int,T}() for _ in 1:n]",
            "get(rows[row], column, zero(T))" => "get(rows[row], column, entry_zero)",
            "row, pivot_column, zero(T), nonzeros" => "row, pivot_column, entry_zero, nonzeros",
            "pivot_row, column, zero(T), nonzeros" => "pivot_row, column, entry_zero, nonzeros",
            "pivot_row, pivot_column, zero(T), nonzeros" => "pivot_row, pivot_column, entry_zero, nonzeros")
    end
    if rational || rational_cache
        source *= "\n_markowitz_threshold_pass(x::Rational{BigInt}, m::Rational{BigInt}) = x >= m / 10\n"
    end
    if rational_cache
        source = replace(source,
            "        column_maximum = _markowitz_column_maximum(column_data)" => "        column_maximum = _markowitz_column_threshold(_markowitz_column_maximum(column_data))",
            "_markowitz_threshold_pass(magnitude, column_maximum) || continue" => "_markowitz_candidate_pass(magnitude, column_maximum) || continue")
        source *= """
        _markowitz_column_threshold(x::Real) = x
        _markowitz_column_threshold(x::Rational{BigInt}) = x / 10
        _markowitz_candidate_pass(x::Real, m::Real) = _markowitz_threshold_pass(x, m)
        _markowitz_candidate_pass(x::Rational{BigInt}, threshold::Rational{BigInt}) = x >= threshold
        """
    end
    return (magnitude ? fast_magnitude : baseline_magnitude) * source
end
variants = [("baseline", (;)), ("zeros", (;zeros=true)),
            ("magnitude", (;magnitude=true)), ("rational10", (;rational=true)),
            ("rational_cache", (;rational_cache=true)),
            ("combined", (;zeros=true,magnitude=true,rational_cache=true))]
modules = Dict{String,Module}()
for (name, options) in variants
    m = Module(Symbol("GenericProbe_",name))
    Core.eval(m, :(using SparseArrays, LinearAlgebra))
    Core.eval(m, :(import JSimplex: _supported_value_type, PFIFactorization, _recycle_pfi_updates!))
    Base.include_string(m, source_variant(;options...), "generic_$name.jl")
    modules[name] = m
end
function fixture(::Type{T}, n, kind) where T
    B = spdiagm(0=>fill(T(4),n))
    if kind == "band"
        B += spdiagm(-1=>fill(-one(T),n-1),1=>fill(-one(T),n-1))
    elseif kind == "fill"
        for i in 1:n, offset in (1,5,13)
            B[i,mod1(i+offset,n)] = -one(T)
        end
    end
    B
end
function equivalent(a,b)
    @test a.sparse_pivots == b.sparse_pivots
    @test a.row_order == b.row_order
    @test a.column_order == b.column_order
    @test isequal(a.diagonal,b.diagonal)
    @test isequal(a.core.factors,b.core.factors)
    for field in (:lower,:upper), (av,bv) in zip(getfield(a,field),getfield(b,field))
        @test av.indices == bv.indices
        @test isequal(av.values,bv.values)
    end
end
rows = Dict{String,Any}[]
@testset "Counterfactual generic checks" begin
    for T in (Float64, BigFloat, Rational{BigInt}), n in (16,32), kind in ("band", "fill")
        B = fixture(T,n,kind)
        before = deepcopy(B)
        reference = modules["baseline"].MarkowitzBackend(B)
        for (name, _) in variants
            m = modules[name]
            run = _ -> (m.MarkowitzBackend(B); nothing)
            result = measure_allocations(run;samples=3)
            merge!(result,Dict("variant"=>name,"value_type"=>string(T),"dimension"=>n,"pattern"=>kind))
            push!(rows,result)
            equivalent(reference,m.MarkowitzBackend(B))
            @test isequal(B,before)
            println(T," ",n," ",kind," ",name," ",result["bytes"]," ",result["allocations"])
            flush(stdout)
        end
    end
    values = setprecision(BigFloat,256) do
        [BigFloat(10)+ldexp(BigFloat(1),-40), -BigFloat(10)-ldexp(BigFloat(1),-40),
         ldexp(BigFloat(1),-1_000_000), -ldexp(BigFloat(1),1_000_000),
         BigFloat(0), -BigFloat(0), BigFloat(Inf), BigFloat(-Inf), BigFloat(NaN), -BigFloat(NaN)]
    end
    for bits in (24,128,512), rounding in (RoundNearest,RoundUp,RoundDown,RoundToZero)
        setprecision(BigFloat,bits) do
            setrounding(BigFloat,rounding) do
                for x in values
                    before=deepcopy(x)
                    a = modules["baseline"]._pivot_magnitude(x)
                    b = modules["combined"]._pivot_magnitude(x)
                    @test isequal(a,b)
                    @test signbit(a)==signbit(b)
                    @test precision(a)==precision(b)
                    @test signbit(x) ? b !== x : b === x
                    @test precision(BigFloat)==bits
                    @test isequal(before,x)
                    @test modules["baseline"]._markowitz_threshold_pass(a,values[1]) ==
                          modules["combined"]._markowitz_threshold_pass(b,values[1])
                end
            end
        end
    end
    # A negative result owns fresh limbs; only that fresh result is mutated.
    original = setprecision(BigFloat,256) do
        -BigFloat(10)-ldexp(BigFloat(1),-40)
    end
    saved = deepcopy(original)
    result = modules["combined"]._pivot_magnitude(original)
    ccall((:mpfr_set_si,Base.MPFR.libmpfr),Cint,
        (Ref{BigFloat},Clong,Base.MPFR.MPFRRoundingMode),result,Clong(1),Base.MPFR.MPFRRoundNearest)
    @test isequal(original,saved)
    @test precision(original)==precision(saved)
    @test result==1
    # Threshold boundary, huge integers, infinities and small denominators.
    for maximum in Rational{BigInt}[0,1,10,big(10)^100//3,1//big(10)^100,1//0],
        magnitude in Rational{BigInt}[0,1,10,big(10)^99//3,1//big(10)^101,1//0]
        a=modules["baseline"]._markowitz_threshold_pass(magnitude,maximum)
        b=modules["combined"]._markowitz_threshold_pass(magnitude,maximum)
        c=modules["combined"]._markowitz_candidate_pass(magnitude,
            modules["combined"]._markowitz_column_threshold(maximum))
        @test a==b==c
    end
end
open(io->TOML.print(io,Dict("rows"=>rows);sorted=true), "diagnostics/markowitz_generic_counterfactual.toml","w")
