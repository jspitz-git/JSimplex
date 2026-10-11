module PipelineCanonicalSupportTests
using JSimplex,Test,SparseArrays,LinearAlgebra
const JS=JSimplex
function workspace(T;manager=:pfi,backend=:native)
    A=sparse(T[1 0 0 0;1 1 0 0;0 0 1 0;0 0 0 1])
    p=JS.LinearProblem(A,zeros(T,4);row_lower=zeros(T,4))
    o=JS.SolverOptions(T;simplex_strategy=:legacy,pricing=:dantzig,
        basis_update=manager,basis_refactorization=backend,verbose=false)
    policy=JS.NumericalPolicy(T;simplex_strategy=:legacy,hypersparse=true,refactor_timing=false)
    return JS.initialize_workspace(p,o;progress=JS.SimplexProgressContext(p;numerical_policy=policy))
end
function canonical(ws,values)
    cache=JS._hypersparse_workspace!(ws);i=JS._pipeline_buffer_index(cache,values)
    v=cache.buffers[i]
    return cache.valid[i] && length(v.indices)==length(unique(v.indices)) &&
        Set(v.indices)==Set(findall(!iszero,values)) &&
        all(v.membership[j]==v.generation for j in v.indices)
end
@testset "Fresh pipeline output retains exact canonical support" begin
    for T in (Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt}),
        manager in (:pfi,:huangfu_hall,:forrest_tomlin,:suhl_suhl,:bartels_golub),backend in (:native,:markowitz)
        ws=workspace(T;manager,backend);cache=JS._hypersparse_workspace!(ws)
        for mode in (:sparse,:dense),transposed in (false,true)
            rhs=JS._pipeline_unit_rhs!(ws,2)
            # Input support may contain a canceled index; the consumer must compact it.
            JS._pipeline_add!(ws,rhs,3,one(T));JS._pipeline_add!(ws,rhs,3,-one(T))
            @test 3 in cache.buffers[1].indices
            out=transposed ? ws.scratch.rho : ws.scratch.row_solution
            JS._pipeline_basis_solve!(out,ws,rhs;transposed,kernel_mode=mode)
            @test out==-T[0,1,0,0]
            @test canonical(ws,out) && !(3 in cache.buffers[1].indices)
            # A canceled structural price must disappear before output density is read.
            rho=ws.scratch.rho;rho.=T[1,-1,0,0];JS._pipeline_changed!(ws,rho)
            JS._pipeline_price!(ws.scratch.tableau_row,ws,rho;kernel_mode=mode)
            @test ws.scratch.tableau_row==T[0,-1,0,0,-1,1,0,0]
            @test canonical(ws,ws.scratch.tableau_row)
            @test JS._pipeline_state(cache,:pricing).output_density==3/8
            # An exact empty producer clears an old nonempty destination.
            JS._pipeline_unit_rhs!(ws,1);JS._pipeline_add!(ws,ws.scratch.row_rhs,1,-one(T))
            JS._pipeline_basis_solve!(out,ws,ws.scratch.row_rhs;transposed,kernel_mode=mode)
            @test all(iszero,out) && canonical(ws,out)
            @test isempty(cache.buffers[JS._pipeline_buffer_index(cache,out)].indices)
        end
    end
end
@testset "Generic output support does not trust validity as canonicality" begin
    ws=workspace(Float64);cache=JS._hypersparse_workspace!(ws)
    rhs=JS._pipeline_unit_rhs!(ws,1)
    JS._pipeline_add!(ws,rhs,2,2.0);JS._pipeline_add!(ws,rhs,1,-1.0)
    @test cache.valid[1] && length(cache.buffers[1].indices)==2
    @test JS._pipeline_output_support!(ws,cache,1,rhs)==1
    @test cache.buffers[1].indices==[2] && cache.buffers[1].membership[1]==0
    # Dense writes and their invalidation continue to require a full rebuild.
    rhs[4]=3;JS._pipeline_changed!(ws,rhs)
    before=cache.support_rebuilds
    @test JS._pipeline_output_support!(ws,cache,1,rhs)==2
    @test cache.support_rebuilds==before+1 && canonical(ws,rhs)
    @test JS._pipeline_output_support!(ws,cache,0,[0.0,-0.0,1.0])==1
    @test_throws OverflowError JS._pipeline_output_support!(ws,cache,0,[1.0,Inf])
end
@testset "Failed sparse production cannot publish valid support" begin
    ws=workspace(Float64);cache=JS._hypersparse_workspace!(ws)
    # Change the owned model before row metadata is built, never reuse stale rows.
    ws.problem.A.nzval[1]=2.0
    rho=ws.scratch.rho;rho[1]=floatmax(Float64);JS._pipeline_changed!(ws,rho)
    @test_throws JS._UnreliableBasisSolve JS._pipeline_price!(ws.scratch.tableau_row,ws,rho;kernel_mode=:sparse)
    @test !cache.valid[5]
    rho[1]=1;JS._pipeline_changed!(ws,rho)
    JS._pipeline_price!(ws.scratch.tableau_row,ws,rho;kernel_mode=:sparse)
    @test ws.scratch.tableau_row==[2.0,0,0,0,-1,0,0,0]
    @test canonical(ws,ws.scratch.tableau_row)
end
end
