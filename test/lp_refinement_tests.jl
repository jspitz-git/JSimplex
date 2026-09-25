using Test, JSimplex, SparseArrays, LinearAlgebra

@testset "LP correction formulation interfaces" begin
    @test isdefined(JSimplex, :build_correction_problem)
    @test isdefined(JSimplex, :_lp_residuals)
end

if isdefined(JSimplex, :build_correction_problem) && isdefined(JSimplex, :_lp_residuals)
    @testset "Exact lifted correction problems reconstruct the original optimum" begin
        T = Rational{BigInt}
        for ranged in (false, true), algorithm in (:primal, :dual)
            p = LinearProblem(sparse(reshape(T[1], 1, 1)), T[1];
                row_lower=T[1], row_upper=T[ranged ? 2 : 1], column_lower=T[0],
                column_upper=[nothing], objective_constant=T(7))
            options = SolverOptions(T; verbose=false, presolve=false, scaling=:off, algorithm)
            ws = JSimplex.initialize_workspace(p, options)
            v = ranged ? T[5//4, 3//2] : T[3//4, 1]
            y = ranged ? T[2] : T[0]
            residuals = JSimplex._lp_residuals(ws, v, y)
            correction, map = JSimplex.build_correction_problem(ws, residuals, T(4), T(8))
            @test correction.A == sparse(T[1 -1])
            @test correction.objective == (ranged ? T[-8, 16] : T[8, 0])
            @test bound_value.(correction.row_lower) == T[1]
            @test correction.row_upper == correction.row_lower
            @test correction.objective_constant == 0
            @test correction.objective_sense == MIN_SENSE
            @test !isfinite(correction.column_upper[1])
            @test map.original_to_correction == [1, 2]
            @test map.correction_to_original == [1, 2, 0]
            @test map.fixed_activities == [3]
            run = algorithm == :primal ?
                JSimplex._solve_continuous_primal(correction, options) :
                JSimplex._solve_continuous_dual(correction, options)
            @test run.status == OPTIMAL
            @test run.primal == (ranged ? T[-1, -2] : T[1, 0])
            reconstructed = v + run.primal / 4
            @test reconstructed == T[1, 1]
            fresh = JSimplex.initialize_from_basis(correction, run.basis, options)
            multiplier = JSimplex._original_dual_witness(fresh)
            @test y + multiplier / 8 == T[1]
            @test p.A == sparse(reshape(T[1], 1, 1))
            @test p.objective == T[1] && p.objective_constant == 7
            @test_throws ArgumentError JSimplex.build_correction_problem(ws, residuals, T(3), T(8))
            @test_throws ArgumentError JSimplex.build_correction_problem(ws, residuals, T(4), T(0))
        end
    end
end
