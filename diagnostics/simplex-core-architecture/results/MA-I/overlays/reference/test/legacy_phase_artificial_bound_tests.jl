using Test, JSimplex, SparseArrays

# Reuse the phase-transfer fixtures: a certified zero auxiliary objective can
# conceal a basic artificial larger than tolerance through retained negatives.
@testset "Legacy phase II normalizes a cancelling artificial point" begin
    for T in (Float32,Float64), manager in (:pfi,:huangfu_hall,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        phase,mapping,original,policy=artificial_bound_fixture(T,manager)
        original.problem.objective .= T[1, 2]
        before=deepcopy((original.problem,original.primal,original.basis.basic_indices))
        count=phase.refactorizations
        @test JSimplex._legacy_primal_point_certified(phase)
        @test sum(phase.primal[mapping.artificial_columns])==zero(T)
        @test maximum(phase.primal[mapping.artificial_columns])>phase.options.primal_tolerance
        result=JSimplex._prepare_legacy_primal_phase_two!(phase,original,2,3,()->false)
        @test isnothing(result)
        @test phase.refactorizations==count+1
        @test original.refactorizations==phase.refactorizations
        @test phase.iterations==original.iterations==1
        @test all(iszero,phase.primal)
        @test JSimplex._legacy_primal_point_certified(phase)
        @test all(j->JSimplex._is_fixed(phase.lower[j],phase.upper[j]),mapping.artificial_columns)
        @test phase.costs[1:2]==original.problem.objective
        @test all(iszero,phase.costs[3:end])
        @test original.primal==before[2] && original.basis.basic_indices==before[3]
        @test original.problem.A==before[1].A && original.problem.column_upper==before[1].column_upper
    end
end

@testset "Legacy phase transfer rejects invalid normalization and honors cancellation" begin
    for mode in (:infeasible,:budget,:iterations,:stop,:late_stop,:exception)
        if mode==:infeasible
            phase,mapping,original,policy=artificial_structural_bound_fixture(Float64,:pfi;infeasible=true)
            n=3
        else
            phase,mapping,original,policy=artificial_bound_fixture(Float64,:pfi;
                max_refinements=mode==:budget ? 0 : 3)
            n=2
        end
        mode==:iterations && (phase.options=JSimplex._remaining_options(phase.options;
            iterations=phase.options.iteration_limit-phase.iterations))
        objective=copy(phase.problem.objective)
        upper=copy(phase.problem.column_upper)
        count=phase.refactorizations
        failure=ArgumentError("legacy transfer cancellation")
        stop=()->begin
            phase.refactorizations>count && mode==:exception && throw(failure)
            mode==:stop || (phase.refactorizations>count && mode==:late_stop)
        end
        result=try JSimplex._prepare_legacy_primal_phase_two!(phase,original,n,3,stop) catch e; e end
        if mode==:exception
            @test result===failure
        else
            @test !isnothing(result)
            @test result.status==(mode in (:stop,:late_stop) ? TIME_LIMIT : mode==:iterations ? ITERATION_LIMIT : NUMERICAL_ERROR)
        end
        @test phase.problem.objective==objective
        @test phase.problem.column_upper==upper
        @test phase.refactorizations==count+(mode in (:infeasible,:late_stop,:exception))
    end
end

@testset "Already removable artificials need no normalization refactorization" begin
    for T in (Float32,Float64)
        phase,mapping,original,policy=artificial_bound_fixture(T,:pfi)
        phase.primal.=zero(T)
        count=phase.refactorizations
        @test isnothing(JSimplex._prepare_legacy_primal_phase_two!(phase,original,2,3,()->false))
        @test phase.refactorizations==count
        @test JSimplex._legacy_primal_point_certified(phase)
    end
end

@testset "Checked legacy transfer keeps its existing recomputation path" begin
    for T in (Float32, Float64)
        phase, mapping, original, policy = artificial_bound_fixture(T, :pfi; pivot_validation=true)
        original.problem.objective .= T[1, 2]
        count = phase.refactorizations
        @test !JSimplex._native_phase_transfer_enabled(phase)
        @test isnothing(JSimplex._prepare_legacy_primal_phase_two!(phase, original, 2, 3, () -> false))
        @test phase.refactorizations == count
        @test phase.progress.numerical_policy === policy
        @test phase.costs[1:2] == original.problem.objective
        @test all(j -> JSimplex._is_fixed(phase.lower[j], phase.upper[j]), mapping.artificial_columns)
    end
end
