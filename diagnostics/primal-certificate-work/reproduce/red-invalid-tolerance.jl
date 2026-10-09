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
    w = PCW_JS._initialize_workspace_state(p,SolverOptions(T;algorithm=:primal,primal_tolerance=zero(T)))
    w.primal[1:3] .= T[3,3,1]
    w.primal[4:end] .= one(T)
    w
end
@testset "Native fallback certificate work and independent state" begin
    for T in (Float32,Float64)
        w=pcw_fallback_workspace(T); n=size(w.problem.A,1)
        for _ in 1:3; @test PCW_JS._legacy_primal_point_certified(w); end
        # Step one retains the materialized Bound vector, but removes native
        # filter scratch and repeated selected-row allocations.
        bytes=@allocated PCW_JS._legacy_primal_point_certified(w)
        @test bytes <= sizeof(JSimplex.Bound{T})*n + 4096
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
