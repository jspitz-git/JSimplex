using Test,JSimplex,SparseArrays,LinearAlgebra

function cancelling_dual_tableau_workspace(;manager=:pfi,diagnostics=nothing,max_refinements=3)
    B=[1.0 1.0;1.3 1.3001]
    a=B[:,1]-1e-6*B[:,2]
    p=LinearProblem(sparse(hcat(B,a)),zeros(3);row_lower=-B[:,2],row_upper=-B[:,2],
        column_lower=[nothing,0.0,0.0])
    options=SolverOptions(algorithm=:dual,basis_update=manager,pricing=:dantzig,verbose=false)
    policy=JSimplex.NumericalPolicy(Float64;max_refinements)
    ws=JSimplex.initialize_workspace(p,options;
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics))
    ws.basis=JSimplex.Basis([1,2],[JSimplex.BASIC,JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER,JSimplex.AT_LOWER])
    JSimplex.recompute!(ws;refactorize=true)
    ws
end

@testset "Native dual tableau recovery retains small pivot information" begin
    for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        ws=cancelling_dual_tableau_workspace(;manager)
        @test ws.primal[2]<-0.9
        terminal=JSimplex.dual_iteration!(ws,()->false)
        @test isnothing(terminal)
        @test ws.iterations==1
        @test ws.basis.basic_indices==[1,3]
        if ws.iterations==1
            @test issuccess(lu(Matrix{Rational{BigInt}}(JSimplex.basis_matrix(ws));check=false))
            @test ws.primal[3]>9e5 && ws.primal[2]==0
            exact=Rational{BigInt}.(ws.problem.A)*Rational{BigInt}.(ws.primal[1:3])
            rhs=Rational{BigInt}.(bound_value.(ws.problem.row_lower))
            @test maximum(abs,exact-rhs)<=Rational{BigInt}(ws.options.primal_tolerance)
            @test JSimplex._original_primal_feasible(ws.problem,ws.primal[1:3],ws.options.primal_tolerance)
        end
    end
end

function prepared_cancelling_tableau(;diagnostics=nothing,max_refinements=3)
    live=cancelling_dual_tableau_workspace(;diagnostics,max_refinements)
    ws=JSimplex._candidate_workspace(live)
    JSimplex.transpose_solve!(ws.scratch.rho,ws.factorization,[0.0,1.0])
    JSimplex.price!(ws.scratch.tableau_row,ws,ws.scratch.rho)
    JSimplex.forward_solve!(ws.scratch.row_solution,ws.factorization,Vector(ws.problem.A[:,3]))
    entering,flips,_=JSimplex._configured_dual_ratio_test(ws,ws.scratch.tableau_row,-1.0,1.0)
    @test entering==3
    live,ws,flips
end

@testset "Native tableau recovery publishes only a complete consistent proposal" begin
    for mode in (:accept,:disabled,:different_flips,:cancel,:throw)
        cancelled=Ref(false)
        observer=(event,ws)->begin
            if event==:correction
                mode==:cancel && (cancelled[]=true)
                mode==:throw && error("tableau correction observer")
            end
            nothing
        end
        diagnostics=JSimplex.SimplexDiagnostics(;observer)
        live,ws,flips=prepared_cancelling_tableau(;diagnostics,max_refinements=mode==:disabled ? 0 : 3)
        mode==:different_flips && push!(flips,4)
        before=(copy(ws.scratch.rho),copy(ws.scratch.row_solution),copy(ws.scratch.tableau_row),copy(flips))
        original=(copy(live.primal),copy(live.costs),copy(live.basis.basic_indices),live.iterations)
        if mode==:throw
            @test_throws JSimplex.DiagnosticObserverFailure{ErrorException} JSimplex._try_native_dual_tableau!(ws,2,3,-1.0,1.0,flips,()->false)
        else
            accepted=JSimplex._try_native_dual_tableau!(ws,2,3,-1.0,1.0,flips,()->cancelled[])
            @test accepted==(mode==:accept)
        end
        if mode!=:accept
            @test before==(ws.scratch.rho,ws.scratch.row_solution,ws.scratch.tableau_row,flips)
        end
        @test original==(live.primal,live.costs,live.basis.basic_indices,live.iterations)
    end
end

@testset "Recovered pivot factors solve the published basis" begin
    for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        ws=cancelling_dual_tableau_workspace(;manager)
        @test isnothing(JSimplex.dual_iteration!(ws,()->false))
        B=JSimplex.basis_matrix(ws)
        rhs=[0.4,-0.7]
        x=JSimplex.forward_solve(ws.factorization,rhs)
        y=JSimplex.transpose_solve(ws.factorization,rhs)
        @test B*x≈rhs atol=1e-5 rtol=1e-5
        @test transpose(B)*y≈rhs atol=1e-5 rtol=1e-5
    end
end

@testset "Split tableau pricing retains native Float32 and Float64 corrections" begin
    for T in (Float32,Float64)
        A=sparse(reshape(T[1.3,1.3],2,1))
        large=T(2)/eps(T)
        rho=T[large,-large];correction=T[1,0]
        out=zeros(T,3)
        @test JSimplex._native_corrected_tableau!(out,A,rho,correction,()->false)
        @test out[1]==T(1.3)
        @test dot(Vector(A[:,1]),rho+correction)==zero(T)
        @test eltype(out)===T
    end
end
