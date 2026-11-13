using JSimplex,Test,SparseArrays,LinearAlgebra

@testset "A rejected weak exchange retains an honest partial postsolve basis" begin
    for T in (Float32,Float64),manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub,:huangfu_hall)
        o=SolverOptions(T;algorithm=:primal,basis_update=manager,verbose=false,
            presolve=false,scaling=:off,simplex_strategy=:legacy)
        p=LinearProblem(sparse(T[1 0;0 0;0 1e9]),zeros(T,2);
            row_lower=[nothing,T(1//8),nothing],row_upper=[one(T),nothing,nothing],
            column_upper=T[2,2])
        w=JSimplex.initialize_workspace(p,o)
        drift=T(1.25)*o.zero_tolerance/T(1e9)
        f=JSimplex._basis_factorization(sparse(T[-1 0 0;0 -1 drift;0 0 -1]),o)
        w.factorization.base=f.base
        result=try
            JSimplex._construct_postsolve_basis!(w,T[1,1],()->false;repair_feasibility=false)
        catch exception
            exception
        end
        @test result isa JSimplex._PostsolveBasisResult
        if result isa JSimplex._PostsolveBasisResult
            @test result.state==JSimplex._POSTSOLVE_PARTIAL && result.exchanges==1
        end
        @test w.basis.basic_indices==[1,4,5]
        @test w.basis.states[2]!=JSimplex.BASIC && w.iterations==0
        # The zero row makes the original LP infeasible. PARTIAL must never
        # masquerade as an accepted point or a certificate for that model.
        @test !JSimplex._original_primal_feasible(p,w.primal[1:2],o.primal_tolerance)
    end
end

@testset "Strong postsolve exchanges request no sensitivity correction solve" begin
    count=Ref(0)
    diag=JSimplex.SimplexDiagnostics(;observer=(event,w)->(event===:correction_attempt && (count[]+=1);nothing))
    p=LinearProblem(sparse([1.0;;]),[0.0];row_upper=[1.0],column_upper=[2.0])
    o=SolverOptions(algorithm=:primal,basis_update=:huangfu_hall,verbose=false,
        presolve=false,scaling=:off,simplex_strategy=:legacy)
    w=JSimplex.initialize_workspace(p,o;progress=JSimplex.SimplexProgressContext(p;diagnostics=diag))
    result=JSimplex._construct_postsolve_basis!(w,[1.0],()->false;repair_feasibility=true)
    @test result.state==JSimplex._POSTSOLVE_ACCEPTED && result.exchanges==1
    @test count[]==0 && w.basis.basic_indices==[1]
end
