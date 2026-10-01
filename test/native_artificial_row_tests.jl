using Test, JSimplex, SparseArrays, LinearAlgebra

# The first basis row has the exactly representable BTRAN solution [1,1,0,0,0,0].
# Native triangular substitution introduces homogeneous roundoff into that row.
function artificial_row_roundoff_fixture(T,manager;diagnostics=nothing,infeasible_original=false,policy_options...)
    A=sparse(T[-3 2 2 1 -3 0; 4 -2 -2 -1 3 0; 1 3 10 0 3 -3;
        -1 0 0 6 -2 1; 2 -3 -2 0 8 -1; -1 -3 1 3 2 4])
    rhs=zeros(T,6)
    policy=JSimplex.NumericalPolicy(T;policy_options...)
    options=SolverOptions(T;algorithm=:primal,basis_update=manager,
        basis_refactorization=:native,verbose=false)
    # Ax=0 has the unique structural solution x=0. A positive original
    # lower bound tests export rejection even after a valid auxiliary exchange.
    lower=zeros(T,6);infeasible_original && (lower[2]=one(T))
    p=LinearProblem(A,zeros(T,6);row_lower=rhs,row_upper=rhs,column_lower=lower)
    auxiliary=LinearProblem(hcat(A,A[:,1:1]),vcat(zeros(T,6),one(T));row_lower=rhs,row_upper=rhs)
    original=JSimplex.initialize_workspace(p,options;
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics))
    phase=JSimplex.initialize_workspace(auxiliary,options;
        progress=JSimplex.SimplexProgressContext(auxiliary;numerical_policy=policy,diagnostics))
    phase.basis=JSimplex.Basis([7,2,3,4,5,6],vcat(JSimplex.AT_LOWER,
        fill(JSimplex.BASIC,6),fill(JSimplex.AT_LOWER,6)))
    JSimplex.recompute!(phase;refactorize=true)
    # Known maintained Phase-I point, independently of its reconstructed solves.
    fill!(phase.primal,zero(T))
    mapping=JSimplex.PhaseOneMap(vcat(1:6,8:13),vcat(1:6,0,7:12),[7])
    return phase,mapping,original,policy
end

@testset "Artificial removal repairs an unreliable native pivot row" begin
    for T in (Float32,Float64), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        phase,mapping,original,policy=artificial_row_roundoff_fixture(T,manager)
        @test JSimplex._legacy_primal_point_certified(phase)
        accepted=JSimplex.remove_artificials!(phase,mapping,original,policy,()->false)
        @test accepted
        if accepted
            @test original.iterations==1
            @test JSimplex._recomputed_basis_reliable(original)
            @test JSimplex._original_primal_feasible(original,original.primal[1:6])
            @test all(j->1<=j<=12,original.basis.basic_indices)
        end
    end
end

@testset "Artificial-row recovery respects budgets and preserves the original on cancellation" begin
    for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        for mode in (:budget,:checked,:dual,:cancel,:exception,:pivot,:point)
            correcting=Ref(false)
            diagnostics=JSimplex.SimplexDiagnostics(;observer=(event,ws)->begin
                event==:correction_attempt && (correcting[]=true)
            end)
            phase,mapping,original,policy=artificial_row_roundoff_fixture(Float64,manager;
                diagnostics,infeasible_original=mode==:point,max_refinements=mode==:budget ? 0 : 3,
                pivot_validation=mode==:checked,
                pivot_error_tolerance=mode==:pivot ? eps(Float64)^2 : sqrt(eps(Float64)))
            mode==:dual && (phase.options=JSimplex._phase_options(phase.options,:dual))
            before=deepcopy((original.basis.basic_indices,original.basis.states,original.primal,
                original.costs,original.lower,original.upper,original.reduced_costs))
            failure=SingularException(927)
            stop=()->begin
                correcting[] && mode==:exception && throw(failure)
                correcting[] && mode==:cancel
            end
            result=try JSimplex.remove_artificials!(phase,mapping,original,policy,stop) catch e; e end
            @test result === (mode==:exception ? failure : false)
            @test isequal(before,(original.basis.basic_indices,original.basis.states,original.primal,
                original.costs,original.lower,original.upper,original.reduced_costs))
            @test original.iterations==(mode==:point ? 1 : 0)
            @test original.refactorizations>=phase.refactorizations
            @test correcting[] == (mode in (:cancel,:exception,:pivot,:point))
            @test JSimplex.event_count(diagnostics,:artificial_removed)==(mode==:point ? 1 : 0)
        end
    end
end

@testset "Reliable artificial rows need no correction budget" begin
    for T in (Float32,Float64,Rational{BigInt}), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        p=LinearProblem(sparse(reshape(T[1],1,1)),T[0];row_lower=T[0],row_upper=T[0])
        auxiliary=LinearProblem(sparse(reshape(T[1,1],1,2)),T[0,1];row_lower=T[0],row_upper=T[0])
        diagnostics=JSimplex.SimplexDiagnostics()
        policy=JSimplex.NumericalPolicy(T;max_refinements=0)
        options=SolverOptions(T;algorithm=:primal,basis_update=manager,verbose=false)
        original=JSimplex.initialize_workspace(p,options;
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics))
        phase=JSimplex.initialize_workspace(auxiliary,options;
            progress=JSimplex.SimplexProgressContext(auxiliary;numerical_policy=policy,diagnostics))
        phase.basis=JSimplex.Basis([2],[JSimplex.AT_LOWER,JSimplex.BASIC,JSimplex.AT_LOWER])
        JSimplex.recompute!(phase;refactorize=true)
        mapping=JSimplex.PhaseOneMap([1,3],[1,0,2],[2])
        @test JSimplex.remove_artificials!(phase,mapping,original,policy,()->false)
        @test original.iterations==1
        @test JSimplex._original_primal_feasible(original,original.primal[1:1])
        @test JSimplex.event_count(diagnostics,:correction_attempt)==0
    end
end
