using Test,JSimplex,SparseArrays

# Two tolerated negative nonbasic artificials hide a positive basic artificial
# in a zero auxiliary objective. Exact nonbasic bounds give the feasible origin.
function artificial_bound_fixture(T,manager;policy_options...)
    policy=JSimplex.NumericalPolicy(T;policy_options...)
    options=SolverOptions(T;algorithm=:primal,basis_update=manager,
        basis_refactorization=:native,verbose=false)
    A=sparse(T[1 1;-1 0;0 -1]);rhs=zeros(T,3)
    problem=LinearProblem(A,zeros(T,2);row_lower=rhs,row_upper=rhs)
    auxiliary=LinearProblem(hcat(A,sparse(T[1 0 0;0 1 0;0 0 1])),T[0,0,1,1,1];
        row_lower=rhs,row_upper=rhs)
    original=JSimplex.initialize_workspace(problem,options;
        progress=JSimplex.SimplexProgressContext(problem;numerical_policy=policy))
    phase=JSimplex.initialize_workspace(auxiliary,options;
        progress=JSimplex.SimplexProgressContext(auxiliary;numerical_policy=policy))
    phase.basis=JSimplex.Basis([3,1,2],vcat(fill(JSimplex.BASIC,3),fill(JSimplex.AT_LOWER,5)))
    JSimplex.recompute!(phase;refactorize=true)
    delta=options.primal_tolerance*T(3)/T(4)
    phase.primal[1:5]=T[-delta,-delta,2delta,-delta,-delta]
    phase.iterations=1
    mapping=JSimplex.PhaseOneMap([1,2,6,7,8],[1,2,0,0,0,3,4,5],[3,4,5])
    return phase,mapping,original,policy
end

@testset "Artificial removal normalizes retained nonbasic bounds only when needed" begin
    for T in (Float32,Float64),manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        phase,mapping,original,policy=artificial_bound_fixture(T,manager)
        @test JSimplex._legacy_primal_point_certified(phase)
        @test JSimplex._original_optimality_certified(phase,phase.primal[1:5])
        @test iszero(sum(phase.primal[mapping.artificial_columns]))
        @test phase.primal[3]>phase.options.primal_tolerance
        accepted=JSimplex.remove_artificials!(phase,mapping,original,policy,()->false)
        @test accepted
        if accepted
            @test original.iterations==2
            @test JSimplex._legacy_primal_point_certified(original)
            @test all(iszero,original.primal)
            @test all(j->j in 1:5,original.basis.basic_indices)
        end
    end
end

function artificial_structural_bound_fixture(T,manager;infeasible=false,upper_retained=false)
    policy=JSimplex.NumericalPolicy(T)
    options=SolverOptions(T;algorithm=:primal,basis_update=manager,
        basis_refactorization=:native,verbose=false)
    delta=options.primal_tolerance*T(3)/T(4)
    sign=upper_retained ? -one(T) : one(T)
    A=sparse(T[1 1 8sign;-1 0 -8sign;0 -1 0])
    rhs=infeasible ? T[-2delta,2delta,0] : zeros(T,3)
    upper=[JSimplex.Bound(zero(T)),JSimplex.Bound{T}(nothing),JSimplex.Bound{T}(nothing)]
    lower=fill(JSimplex.Bound(zero(T)),3)
    if upper_retained
        lower[3]=JSimplex.Bound{T}(nothing);upper[3]=JSimplex.Bound(zero(T))
    end
    problem=LinearProblem(A,zeros(T,3);row_lower=rhs,row_upper=rhs,column_lower=lower,column_upper=upper)
    auxiliary=LinearProblem(hcat(A,sparse(T[1 0 0;0 1 0;0 0 1])),T[0,0,0,1,1,1];
        row_lower=rhs,row_upper=rhs,column_lower=vcat(lower,fill(JSimplex.Bound(zero(T)),3)),
        column_upper=vcat(upper,fill(JSimplex.Bound{T}(nothing),3)))
    original=JSimplex.initialize_workspace(problem,options;
        progress=JSimplex.SimplexProgressContext(problem;numerical_policy=policy))
    phase=JSimplex.initialize_workspace(auxiliary,options;
        progress=JSimplex.SimplexProgressContext(auxiliary;numerical_policy=policy))
    states=fill(JSimplex.AT_LOWER,9);states[[4,1,2]].=JSimplex.BASIC
    upper_retained && (states[3]=JSimplex.AT_UPPER)
    phase.basis=JSimplex.Basis([4,1,2],states)
    JSimplex.recompute!(phase;refactorize=true)
    phase.primal[1:6]=T[infeasible ? -delta : delta,-delta,-sign*delta/4,2delta,-delta,-delta]
    phase.iterations=1
    mapping=JSimplex.PhaseOneMap([1,2,3,7,8,9],[1,2,3,0,0,0,4,5,6],[4,5,6])
    return phase,mapping,original,policy
end

@testset "Exact structural bounds require a complete point certificate" begin
    for T in (Float32,Float64),manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub),infeasible in (false,true),upper_retained in (false,true)
        phase,mapping,original,policy=artificial_structural_bound_fixture(T,manager;infeasible,upper_retained)
        @test JSimplex._legacy_primal_point_certified(phase)
        @test JSimplex._original_optimality_certified(phase,phase.primal[1:6])
        @test iszero(sum(phase.primal[mapping.artificial_columns]))
        before=deepcopy((original.primal,original.basis.basic_indices,original.basis.states,
            original.costs,original.lower,original.upper,original.reduced_costs))
        count=phase.refactorizations
        @test JSimplex.remove_artificials!(phase,mapping,original,policy,()->false)==!infeasible
        @test original.refactorizations>count
        if infeasible
            @test isequal(before,(original.primal,original.basis.basic_indices,original.basis.states,
                original.costs,original.lower,original.upper,original.reduced_costs))
            @test original.iterations==1
        else
            @test all(iszero,original.primal)
            @test JSimplex._legacy_primal_point_certified(original)
        end
    end
end

@testset "Artificial normalization respects policy, budgets and cancellation" begin
    for mode in (:budget,:checked,:dual,:iterations,:stop,:late_stop,:exception)
        phase,mapping,original,policy=artificial_bound_fixture(Float64,:pfi;
            max_refinements=mode==:budget ? 0 : 3,pivot_validation=mode==:checked)
        mode==:dual && (phase.options=JSimplex._phase_options(phase.options,:dual))
        mode==:iterations && (phase.options=JSimplex._remaining_options(phase.options;
            iterations=phase.options.iteration_limit-phase.iterations))
        before=deepcopy((original.primal,original.basis.basic_indices,original.basis.states,
            original.costs,original.lower,original.upper,original.reduced_costs))
        count=phase.refactorizations
        failure=ArgumentError("normalization stop")
        stop=()->begin
            phase.refactorizations>count && mode==:exception && throw(failure)
            mode==:stop || (phase.refactorizations>count && mode==:late_stop)
        end
        result=try JSimplex.remove_artificials!(phase,mapping,original,policy,stop) catch e; e end
        @test result === (mode==:exception ? failure : false)
        @test isequal(before,(original.primal,original.basis.basic_indices,original.basis.states,
            original.costs,original.lower,original.upper,original.reduced_costs))
        @test original.iterations==1
        @test original.refactorizations==count+(mode in (:late_stop,:exception))
    end
    for T in (Float32,Float64)
        phase,mapping,original,policy=artificial_bound_fixture(T,:pfi)
        phase.primal./=T(4)
        before=copy(phase.primal);count=phase.refactorizations
        @test JSimplex._normalize_phase_artificial_bounds!(phase,mapping,original,policy,()->false)
        @test phase.primal==before
        @test phase.refactorizations==count
    end
end

@testset "Earlier exchanges may make a later artificial removable without normalization" begin
    for T in (Float32,Float64),manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub),mode in (:native,:budget,:checked)
        tolerance=T(2)^(-20)
        rhs=T[tolerance/2,5tolerance/4]
        A=sparse(reshape(T[1,1],2,1))
        problem=LinearProblem(A,T[0];row_lower=rhs,row_upper=rhs)
        auxiliary=LinearProblem(hcat(A,sparse(T[1 0;0 1])),T[0,1,1];row_lower=rhs,row_upper=rhs)
        options=SolverOptions(T;algorithm=:primal,basis_update=manager,
            primal_tolerance=tolerance,verbose=false)
        policy=JSimplex.NumericalPolicy(T;max_refinements=mode==:budget ? 0 : 3,
            pivot_validation=mode==:checked)
        original=JSimplex.initialize_workspace(problem,options;
            progress=JSimplex.SimplexProgressContext(problem;numerical_policy=policy))
        phase=JSimplex.initialize_workspace(auxiliary,options;
            progress=JSimplex.SimplexProgressContext(auxiliary;numerical_policy=policy))
        phase.basis=JSimplex.Basis([2,3],[JSimplex.AT_LOWER,JSimplex.BASIC,JSimplex.BASIC,
            JSimplex.AT_LOWER,JSimplex.AT_LOWER])
        JSimplex.recompute!(phase;refactorize=true)
        mapping=JSimplex.PhaseOneMap([1,4,5],[1,0,0,2,3],[2,3])
        @test phase.primal[3]>tolerance
        @test !JSimplex._normalize_phase_artificial_bounds!(deepcopy(phase),mapping,deepcopy(original),policy,()->false)
        @test JSimplex.remove_artificials!(phase,mapping,original,policy,()->false)
        @test original.iterations==2
        @test JSimplex._original_primal_feasible(original,original.primal[1:1])
    end
end
