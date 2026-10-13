using LinearAlgebra, SparseArrays, Random

@testset "Long residuals use bounded native scratch" begin
    # Long dot products previously allocated BigFloat values solely because
    # their pessimistic rounding bound exceeded a fixed fraction of tolerance.
    for T in (Float32, Float64), transposed in (false, true)
        row = repeat(T[2^20, 1, -2^20], 100)
        B = sparse(transposed ? reshape(row,:,1) : reshape(row,1,:))
        x = ones(T,300)
        rhs = T[100]
        scratch = JSimplex.SolveQualityScratch(T,1)
        policy = JSimplex.NumericalPolicy(T)
        check() = JSimplex.solve_quality!(scratch,B,x,rhs,policy;transposed)
        quality = check()
        @test quality.reliable && quality.finite
        @test scratch.residual == T[0]
        @test (@allocated check()) <= 4096
        rhs[1] = T(1_000_000)
        @test !check().reliable
        @test scratch.residual == T[999900]
    end
end

@testset "Native residual acceptance agrees with exact input arithmetic" begin
    rng = MersenneTwister(47021)
    for T in (Float32,Float64), transposed in (false,true), exponent in (-20,0,20)
        B = sparse(T.(randn(rng,8,80)) .* T(2)^exponent)
        M = transposed ? transpose(B) : B
        x = T.(randn(rng,size(M,2)))
        rhs = M*x
        policy = JSimplex.NumericalPolicy(T)
        scratch = JSimplex.SolveQualityScratch(T,length(rhs))
        for perturbation in (zero(T), T(0.01)*maximum(abs,rhs))
            trial = copy(rhs); trial[1] += perturbation
            quality = JSimplex.solve_quality!(scratch,B,x,trial,policy;transposed)
            exact_M = Rational{BigInt}.(Matrix(M))
            exact_x,exact_rhs = Rational{BigInt}.(x),Rational{BigInt}.(trial)
            residual = exact_rhs-exact_M*exact_x
            scale = abs.(exact_rhs)+abs.(exact_M)*abs.(exact_x)
            error = maximum(abs.(residual)./scale)
            @test quality.finite
            @test quality.reliable == (error <= Rational{BigInt}(policy.solve_tolerance))
        end
    end
end

struct CountedQualityVector{T} <: AbstractVector{T}
    values::Vector{T}
    reads::Base.RefValue{Int}
end
Base.size(x::CountedQualityVector) = size(x.values)
Base.IndexStyle(::Type{<:CountedQualityVector}) = IndexLinear()
function Base.getindex(x::CountedQualityVector,i::Int)
    x.reads[] += 1
    return x.values[i]
end

@testset "Compensated pricing audits retain sparse traversal" begin
    for T in (Float32,Float64), transposed in (false,true)
        A = sparse(1:64,ones(Int,64),ones(T,64),64,80)
        B = JSimplex._PriceAuditMatrix(A)
        M = transposed ? transpose(Matrix(B)) : Matrix(B)
        values = ones(T,size(M,2))
        rhs = M*values
        x = CountedQualityVector(values,Ref(0))
        scratch = JSimplex.SolveQualityScratch(T,length(rhs))
        policy = JSimplex.NumericalPolicy(T)
        quality = JSimplex._compensated_solve_quality!(scratch,B,x,rhs,policy,transposed)
        @test !isnothing(quality) && quality.reliable
        @test all(iszero,scratch.residual)
        # One input access per stored coefficient or implicit identity entry.
        # The previous fallback visited the entire implicit dense rectangle.
        @test x.reads[] == nnz(A)+2size(A,1)+size(A,2)
    end
end

@testset "Native acceptance boundary falls back to an exact-input check" begin
    for T in (Float32,Float64), transposed in (false,true)
        B = reshape(T[1],1,1); x = T[1]; rhs = T[1+8eps(T)]
        exact_error = (Rational{BigInt}(rhs[1])-1)/(Rational{BigInt}(rhs[1])+1)
        center = T(exact_error)
        for tolerance in (prevfloat(center),center,nextfloat(center))
            policy = JSimplex.NumericalPolicy(T;solve_tolerance=tolerance)
            scratch = JSimplex.SolveQualityScratch(T,1)
            @test isnothing(JSimplex._compensated_solve_quality!(scratch,B,x,rhs,policy,transposed))
            quality = JSimplex.solve_quality!(scratch,B,x,rhs,policy;transposed)
            @test quality.finite
            @test quality.reliable == (exact_error <= Rational{BigInt}(tolerance))
        end
    end
end

@testset "Direct wide refinement retains exceptional-range recovery" begin
    tiny = nextfloat(0.0)
    for (B,x,rhs,exact_error) in (
        (reshape([floatmin(Float64)],1,1),[floatmin(Float64)],[0.0],1//big(1)),
        ([1e308 -1e308],[2.0,2.0],[0.0],0//big(1)),
        (reshape([tiny],1,1),[0.75],[tiny],1//big(7)))
        scratch = JSimplex.SolveQualityScratch(Float64,1)
        policy = JSimplex.NumericalPolicy(Float64)
        @test isnothing(JSimplex._compensated_solve_quality!(scratch,B,x,rhs,policy,false))
        quality = JSimplex._refinement_quality!(scratch,B,x,rhs,policy,false,true)
        @test quality.finite
        @test quality.reliable == (exact_error <= Rational{BigInt}(policy.solve_tolerance))
    end
end
