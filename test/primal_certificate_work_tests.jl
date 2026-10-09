using Test, JSimplex, SparseArrays, Random
const PCW_JS = JSimplex
function pcw_fallback_workspace(::Type{T}, n=2048) where T
    # Opposite long sums widen the ordinary interval while the compensated
    # native row filter certifies exactly cancelling terms.
    a = T(0.1)
    A = sparse(repeat(collect(1:n), 3), vcat(fill(1,n),fill(2,n),fill(3,n)),
               vcat(fill(a,n),fill(-a,n),ones(T,n)), n, 3)
    p = LinearProblem(A, zeros(T,3); column_lower=zeros(T,3),
        row_lower=ones(T,n),row_upper=ones(T,n))
    w = PCW_JS._initialize_workspace_state(p,SolverOptions(T;algorithm=:primal,primal_tolerance=eps(T)^2))
    w.primal[1:3] .= T[3,3,1]
    w.primal[4:end] .= one(T)
    w
end
@testset "Native fallback certificate work and independent state" begin
    for T in (Float32,Float64)
        w=pcw_fallback_workspace(T); n=size(w.problem.A,1)
        for _ in 1:3; @test PCW_JS._legacy_primal_point_certified(w); end
        # Repeated native-only fallback must not allocate a full activity-bound
        # vector or rebuild filter scratch.
        bytes=@allocated PCW_JS._legacy_primal_point_certified(w)
        @test bytes <= 512
        w.primal[1]=nextfloat(w.primal[1])
        @test !PCW_JS._legacy_primal_point_certified(w)
        w.primal[1]=T(3)
        @test PCW_JS._legacy_primal_point_certified(w)
        w.primal[4]=nextfloat(one(T))
        @test !PCW_JS._legacy_primal_point_certified(w)
        w.primal[4]=one(T)
        @test PCW_JS._legacy_primal_point_certified(w)
        w.problem.A.nzval[1]=T(NaN)
        @test !PCW_JS._legacy_primal_point_certified(w)
        w.problem.A.nzval[1]=T(0.1)
        @test PCW_JS._legacy_primal_point_certified(w)
        other=pcw_fallback_workspace(T,32)
        @test PCW_JS._legacy_primal_point_certified(other)
        @test other.scratch.primal_point_buffers !== w.scratch.primal_point_buffers
    end
end

@testset "Activity bound view preserves indexed values and checks" begin
    for T in (Float32,Float64)
        values=T[3,0,-0.0,1,-2,5,6]
        bounds=PCW_JS._PrimalActivityBounds(values,1)
        @test size(bounds)==(6,)
        @test isequal(collect(bounds),Bound.(values[2:end]))
        @test_throws BoundsError bounds[0]
        @test_throws BoundsError bounds[7]
        values[4]=T(5)
        @test bounds[3]==Bound(T(5))
        for bad in (T(Inf),T(-Inf),T(NaN))
            values[end]=bad
            @test_throws ArgumentError bounds[end]
        end
    end
end

struct PCWCountingBounds{T} <: AbstractVector{Bound{T}}
    values::Vector{Bound{T}}
    reads::Base.RefValue{Int}
end
Base.size(b::PCWCountingBounds)=size(b.values)
Base.getindex(b::PCWCountingBounds,i::Int)=(b.reads[]+=1;b.values[i])
@testset "Owned row selection scans a certified prefix only once" begin
    n=32; p=LinearProblem(spdiagm(0=>ones(n)),zeros(n);row_lower=ones(n),row_upper=ones(n))
    lo=ones(n);hi=ones(n);lo[end]=0;hi[end]=2
    bounds=PCWCountingBounds(p.row_lower,Ref(0))
    buffers=PCW_JS._PrimalPointBuffers(zeros(n),zeros(n),zeros(n))
    @test PCW_JS._primal_feasible_with_bounds(p,ones(n),1e-7,p.column_lower,p.column_upper,bounds,p.row_upper,(lo,hi),buffers)
    @test bounds.reads[] <= n+4
end
