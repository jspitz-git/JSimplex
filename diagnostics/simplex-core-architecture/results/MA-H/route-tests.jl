# UNEXECUTED MA-H tests. Include after the unchanged candidate-tests.jl, under
# the independently admitted scoped Test collector. No global method overwrite.
module MarkowitzMARoutingTests
using Test
using JSimplex
using JSimplex.LinearAlgebra
const J = JSimplex
const MarkowitzBackend = J.MarkowitzBackend
const Old = Main.MarkowitzMAUpperTests
include("reference-forward.jl")
observed(v) = [(deepcopy(x), x isa BigFloat ? precision(x) : 0, signbit(x)) for x in v]
upper_state(b) = [(copy(row.indices), observed(row.values)) for row in b.upper]
function outcome(f, destination, backend, rhs)
    try
        f(destination, backend, rhs)
        return nothing
    catch err
        return typeof(err)
    end
end
function compare_forward(::Type{T}, family; special=:none) where T
    A = family === :star ? Old.star(T,8) : Matrix{T}(I,3,3) + fill(one(T),3,3)
    b = J.MarkowitzBackend(A)
    rhs = A * ones(T,size(A,1))
    expected_error = nothing
    if special === :signedzero
        fill!(rhs,zero(T)); rhs[1] = -zero(T)
    elseif special === :inf
        rhs[1] = T(Inf)
    elseif special === :nan
        rhs[1] = T(NaN)
    elseif special === :zero_inf
        fill!(rhs,zero(T)); b.upper[1].values[1] = BigInt(1)//BigInt(0)
        expected_error = DivideError
    elseif special === :bounds
        b.upper[1].indices[end] = length(rhs)+1
        expected_error = BoundsError
    elseif special === :rounding
        rhs = T[T(j)/T(3) for j in eachindex(rhs)]
    end
    c = J._copy_backend(b)
    sentinel = T(-99)
    expected = fill(sentinel,length(rhs)); actual = fill(sentinel,length(rhs))
    before_rhs = observed(rhs); before_upper = upper_state(b); before_diagonal = observed(b.diagonal)
    er = outcome(reference_forward!,expected,b,rhs)
    ec = outcome(J._backend_forward_solve!,actual,c,rhs)
    @test b.sparse_pivots == (family === :star ? 6 : 0)
    @test b.work !== c.work
    @test er === expected_error
    @test ec === er
    @test isequal(observed(expected),observed(actual)) && (expected_error === nothing || all(x->isequal(x,sentinel),expected))
    @test isequal(observed(b.work),observed(c.work))
    @test isequal(observed(rhs),before_rhs)
    @test isequal(upper_state(b),before_upper) && isequal(upper_state(c),before_upper)
    @test isequal(observed(b.diagonal),before_diagonal) && isequal(observed(c.diagonal),before_diagonal)
    return nothing
end
@testset "MA route complete forward" begin
    for T in (Float32,Float64,Rational{Int},Rational{BigInt})
        for family in (:star,:core); compare_forward(T,family); end
    end
    for bits in (128,256,512)
        setprecision(BigFloat,bits) do
            for family in (:star,:core); compare_forward(BigFloat,family); end
        end
    end
end
@testset "MA route exceptional forward" begin
    setprecision(BigFloat,128) do
        for special in (:signedzero,:inf,:nan)
            compare_forward(BigFloat,:star;special=special)
        end
        compare_forward(Rational{BigInt},:star;special=:zero_inf)
        for T in (BigFloat,Rational{BigInt}); compare_forward(T,:star;special=:bounds); end
    end
end
@testset "MA route scoped rounding forward" begin
    before_rounding = rounding(BigFloat); before_global = Base.MPFR.ROUNDING_MODE[]
    setprecision(BigFloat,128) do
        for mode in (RoundDown,RoundUp,RoundToZero,RoundNearest)
            setrounding(BigFloat,mode) do
                @test J._markowitz_ma_rounding_matches() == (Base.MPFR.rounding_raw(BigFloat) == before_global)
                compare_forward(BigFloat,:star;special=:rounding)
                setrounding(BigFloat,RoundUp) do
                    @test J._markowitz_ma_rounding_matches() == (Base.MPFR.rounding_raw(BigFloat) == before_global)
                    compare_forward(BigFloat,:star;special=:rounding)
                end
                @test rounding(BigFloat) == mode
            end
        end
    end
    @test rounding(BigFloat) == before_rounding
    @test Base.MPFR.ROUNDING_MODE[] == before_global
end
end # module
