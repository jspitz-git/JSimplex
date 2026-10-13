# UNEXECUTED MA-D candidate tests. Load only in the future admitted test process.
module MarkowitzMAUpperTests
using Test
using JSimplex
using JSimplex.LinearAlgebra
using JSimplex.SparseArrays
const J = JSimplex
const PV = J.PackedFactorVector
const available = isdefined(J, :_markowitz_upper_solve!) &&
                  isdefined(J, :_markowitz_ma_scratch)

# Exact original ordered arithmetic, independent of candidate helpers.
function reference!(work, upper, diagonal, count)
    for pivot in count:-1:1
        value = work[pivot]
        row = upper[pivot]
        for index in eachindex(row.indices)
            value -= row.values[index] * work[row.indices[index]]
        end
        work[pivot] = value / diagonal[pivot]
    end
    return work
end
function outcome(f, work, upper, diagonal, count)
    try
        f(work, upper, diagonal, count)
        return nothing
    catch err
        return typeof(err)
    end
end
function compare(work, upper, diagonal, count)
    a, b = deepcopy(work), deepcopy(work)
    ea = outcome(reference!, a, upper, diagonal, count)
    eb = outcome(J._markowitz_upper_solve!, b, upper, diagonal, count)
    @test ea == eb
    @test isequal(a, b)
    if eltype(work) === BigFloat
        @test precision.(a) == precision.(b)
        @test signbit.(a) == signbit.(b)
    end
    return b
end
leaves(x::BigFloat) = Any[getfield(x, :d)]
leaves(x::BigInt) = Any[x]
leaves(x::Rational{BigInt}) = Any[numerator(x), denominator(x)]
leaves(x::Tuple) = reduce(vcat, (leaves(v) for v in x); init=Any[])
function star(::Type{T}, n) where T
    A = Matrix{T}(I, n, n) .* T(2)
    for j in 2:n
        A[1,j] = T(isodd(j) ? -1 : 1) / T(8)
    end
    return A
end
function singleton_row(::Type{T}, values=T[1,1]) where T
    return PV{T}[PV{T}([2,3], values)]
end

@testset "MA upper dispatch and fallback" begin
    @test isdefined(J, :_markowitz_upper_solve!)
    @test isdefined(J, :_markowitz_ma_scratch)
    if available
        for T in (Float32, Float64, Rational{Int}, BigFloat, Rational{BigInt})
            for k in 0:2
                upper = PV{T}[PV{T}(collect(2:1+k), T.(1:k))]
                compare(T[7,2,3], upper, T[2], 1)
            end
            compare(T[], PV{T}[], T[], 0)
            b = J.MarkowitzBackend(Matrix{T}(I,3,3) + fill(one(T),3,3))
            @test b.sparse_pivots == 0
            out = zeros(T,3)
            J._backend_forward_solve!(out,b,fill(T(4),3))
            @test out == ones(T,3)
        end
        m64 = which(J._markowitz_upper_solve!, (Vector{Float64},Vector{PV{Float64}},Vector{Float64},Int))
        mbf = which(J._markowitz_upper_solve!, (Vector{BigFloat},Vector{PV{BigFloat}},Vector{BigFloat},Int))
        mrq = which(J._markowitz_upper_solve!, (Vector{Rational{BigInt}},Vector{PV{Rational{BigInt}}},Vector{Rational{BigInt}},Int))
        @test mbf !== m64
        @test mrq !== m64
    end
end

if available
@testset "MA upper scalar ownership" begin
    for T in (BigFloat, Rational{BigInt})
        for seedvalue in (0,3)
            shared = T(seedvalue)
            work = T[shared,shared,shared]
            upper = singleton_row(T,T[shared,shared])
            diagonal = T[one(T)]
            retained = Any[shared,upper[1].values...,diagonal...]
            before = deepcopy(retained)
            input_leaves = reduce(vcat,leaves.(retained);init=Any[])
            acc, buffer = J._markowitz_ma_scratch(T)
            own = leaves((acc,buffer))
            @test length(own) == (T === BigFloat ? 2 : 12)
            @test all(own[i] !== own[j] for i in eachindex(own) for j in 1:i-1)
            @test all(a !== b for a in own for b in input_leaves)
            expected = reference!(deepcopy(work),upper,diagonal,1)
            J._markowitz_upper_solve!(work,upper,diagonal,1)
            @test isequal(work,expected)
            @test isequal(retained,before)
            @test all(a !== b for a in leaves(work[1]) for b in input_leaves)
            saved = work[1]; saved_value = deepcopy(saved)
            J._markowitz_upper_solve!(work,upper,diagonal,1)
            @test isequal(saved,saved_value)
        end
    end
    # Deliberately shared BigInt leaves, not merely equal rational values.
    num, den = BigInt(2), BigInt(3)
    a = Base.unsafe_rational(num,den)
    b = Base.unsafe_rational(den,BigInt(5))
    @test numerator(b) === denominator(a)
    work = Rational{BigInt}[a,b,a]
    upper = singleton_row(Rational{BigInt},Rational{BigInt}[a,b])
    before = deepcopy((a,b))
    J._markowitz_upper_solve!(work,upper,Rational{BigInt}[b],1)
    @test (a,b) == before
    @test all(x !== y for x in leaves(work[1]) for y in leaves((a,b)))
end

@testset "MA upper sequential arithmetic" begin
    for bits in (128,256,512)
        setprecision(BigFloat,bits) do
            seed = setprecision(BigFloat,bits+32) do
                one(BigFloat) + BigFloat(2)^(-bits-2)
            end
            upper = singleton_row(BigFloat,BigFloat[1,0])
            result = compare(BigFloat[seed,1,-0.0],upper,BigFloat[1],1)
            @test result[1] == BigFloat(2)^(-bits-2)
            @test BigFloat(seed;precision=bits) - one(BigFloat) == 0
            for s in (BigFloat(0),-BigFloat(0),BigFloat(7)/3)
                compare(BigFloat[s,2,-2],singleton_row(BigFloat),BigFloat[3],1)
            end
            # A prefix-at-a-time run compares every published row with original.
            upper3 = PV{BigFloat}[PV{BigFloat}([2,3],BigFloat[1,2]),PV{BigFloat}([3,4],BigFloat[3,4]),PV{BigFloat}([4,4],BigFloat[1,-1])]
            for count in 1:3
                compare(BigFloat[9,7,5,2],upper3,BigFloat[2,3,4],count)
            end
        end
    end
    T=Rational{BigInt}
    for k in (8,256,1024)
        a=(BigInt(2)^k+1)//(BigInt(2)^k-1)
        compare(T[a,a,-a],singleton_row(T,T[a,a]),T[3//7],1)
    end
end

@testset "MA upper rounding fallback" begin
    global_before = J.Base.MPFR.ROUNDING_MODE[]
    ambient_before = rounding(BigFloat)
    for mode in (RoundDown,RoundUp,RoundToZero,RoundNearest)
        setrounding(BigFloat,mode) do
            @test J._markowitz_ma_rounding_matches() == (J.Base.MPFR.rounding_raw(BigFloat) == global_before)
            compare(BigFloat[1,1//3,1//7],singleton_row(BigFloat),BigFloat[3],1)
            setrounding(BigFloat,RoundUp) do
                compare(BigFloat[-0.0,1//9,1//11],singleton_row(BigFloat),BigFloat[7],1)
            end
            @test rounding(BigFloat) == mode
        end
    end
    @test rounding(BigFloat) == ambient_before
    @test J.Base.MPFR.ROUNDING_MODE[] == global_before
end

@testset "MA upper exceptions" begin
    T=Rational{BigInt};inf=BigInt(1)//BigInt(0)
    for diagonal in (T[],Vector{T}(undef,1))
        work=T[1,0,1];upper=singleton_row(T,T[inf,1])
        @test !J._markowitz_ma_row_eligible(work[1],upper[1],work,diagonal,1)
        @test outcome(reference!,copy(work),upper,diagonal,1) === DivideError
        @test outcome(J._markowitz_upper_solve!,copy(work),upper,diagonal,1) === DivideError
        compare(work,upper,diagonal,1)
    end
    for diagonal in (T[0],T[inf],T[1])
        compare(T[0,0,0],singleton_row(T),diagonal,1)
        compare(T[1,2,3],singleton_row(T,T[inf,1]),diagonal,1)
    end
    for T in (BigFloat,Rational{BigInt})
        for upper in (PV{T}[PV{T}([2,9],T[1,1])],PV{T}[PV{T}([2,3],T[1])],PV{T}[PV{T}([2,3],Vector{T}(undef,2))])
            compare(T[1,2,3],upper,T[1],1)
        end
        # Row2 is published before row1 fails; row1 remains unmodified.
        upper=PV{T}[PV{T}([2,99],T[1,1]),PV{T}([3,4],T[1,1])]
        compare(T[9,8,3,2],upper,T[1,1],2)
    end
    for v in (BigFloat(NaN),BigFloat(Inf),-BigFloat(Inf),floatmax(BigFloat),floatmin(BigFloat),-BigFloat(0))
        compare(BigFloat[v,2,0],singleton_row(BigFloat,BigFloat[v,0]),BigFloat[1],1)
    end
end

@testset "MA upper lifecycle" begin
    for bits in (128,512,128)
        setprecision(BigFloat,bits) do
            for T in (BigFloat,Rational{BigInt})
                A=star(T,8);factor=J.PFIFactorization(sparse(A),Val(:markowitz))
                @test factor.base.sparse_pivots == 6
                @test count(v->length(v.indices)>=2,factor.base.upper) == 1
                @test sum(length(v.indices) for v in factor.base.upper) == 7
                rhs=A*ones(T,8);saved=deepcopy(rhs)
                out=J.forward_solve(factor,rhs)
                @test out == ones(T,8)
                copied=J.copy_basis_factorization(factor)
                @test copied.base.work !== factor.base.work
                for f in (factor,copied)
                    J.forward_solve!(out,f,rhs)
                    @test rhs == saved
                    @test out == ones(T,8)
                    J.refactorize!(f,sparse(A))
                    inplace=copy(rhs)
                    J.forward_solve!(inplace,f,inplace)
                    @test inplace == ones(T,8)
                end
            end
        end
    end
end
end # available
end # module
