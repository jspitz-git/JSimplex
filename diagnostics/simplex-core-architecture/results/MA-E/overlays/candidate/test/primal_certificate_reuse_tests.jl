using Test, JSimplex, SparseArrays, LinearAlgebra

# Frozen composition of the independent checks before enclosure reuse.
function separate_primal_point_certificate(ws)
    tolerance=ws.options.primal_tolerance
    JSimplex._finite_workspace(ws) || return false
    for i in eachindex(ws.primal)
        max(JSimplex._lower_violation(ws.lower[i],ws.primal[i]),
            JSimplex._upper_violation(ws.upper[i],ws.primal[i])) <= tolerance || return false
    end
    JSimplex._legacy_primal_model_feasible(ws) &&
        JSimplex._legacy_primal_row_consistent(ws,tolerance)
end

function certificate_reuse_workspace(T;m=128,n=512)
    A=sparse([mod1(j,m) for j in 1:n],collect(1:n),ones(T,n),m,n)
    problem=LinearProblem(A,zeros(T,n);row_lower=zeros(T,m),row_upper=fill(T(10),m))
    ws=JSimplex.initialize_workspace(problem,SolverOptions(T;algorithm=:primal,verbose=false))
    ws.primal[1:n].=one(T);ws.primal[n+1:end].=A*ones(T,n)
    ws
end

@testset "Shared primal enclosures preserve both independent certificates" begin
    for T in (Float32,Float64)
        ws=certificate_reuse_workspace(T;m=2,n=8)
        for delta in (zero(T),ws.options.primal_tolerance/T(4),T(1),T(NaN))
            ws.primal[end]=T(4)+delta
            @test JSimplex._legacy_primal_point_certified(ws)==separate_primal_point_certificate(ws)
        end
        # Working bounds alone must not silently replace the original model.
        ws.primal[end]=T(4);ws.primal[1]=T(20);ws.primal[9]=T(23)
        ws.upper[9]=Bound(T(30))
        @test !JSimplex._legacy_primal_point_certified(ws)
        @test !separate_primal_point_certificate(ws)
        journal=JSimplex.PerturbationJournal(ws)
        journal.bounds=JSimplex.BoundPerturbationState(ws)
        journal.bounds.active_upper[9]=Bound(T(30));journal.bounds.active=true
        ws.lower=journal.bounds.active_lower;ws.upper=journal.bounds.active_upper
        ws.scratch.perturbations=journal
        @test JSimplex._legacy_primal_point_certified(ws)
        @test separate_primal_point_certificate(ws)
        journal.workspace_id=UInt(0)
        @test_throws ArgumentError JSimplex._legacy_primal_point_certified(ws)
        @test_throws ArgumentError separate_primal_point_certificate(ws)

        magnitude=T===Float32 ? T(1e8) : T(1e16)
        p=LinearProblem(sparse(reshape(T[magnitude,1,-magnitude],1,3)),zeros(T,3);
            row_lower=T[1],row_upper=T[1])
        ws=JSimplex.initialize_workspace(p,SolverOptions(T;algorithm=:primal,verbose=false))
        ws.primal.=one(T)
        @test JSimplex._legacy_primal_point_certified(ws)
        @test separate_primal_point_certificate(ws)
        ws.primal[end]=T(2)
        @test !JSimplex._legacy_primal_point_certified(ws)
        @test !separate_primal_point_certificate(ws)
    end
end

@testset "Primal point certificate avoids duplicate enclosure allocations" begin
    ws=certificate_reuse_workspace(Float64)
    @test separate_primal_point_certificate(ws)
    @test JSimplex._legacy_primal_point_certified(ws)
    separate_primal_point_certificate(ws);JSimplex._legacy_primal_point_certified(ws)
    separate_bytes=@allocated separate_primal_point_certificate(ws)
    reused_bytes=@allocated JSimplex._legacy_primal_point_certified(ws)
    m,n=size(ws.problem.A)
    @test reused_bytes+sizeof(Float64)*(2m+n)<=separate_bytes+512
end
