using Test, JSimplex

@testset "Opt-in kernel timing preserves results and counts exceptions" begin
    @test isdefined(JSimplex, :_diagnostic_kernel)
    if isdefined(JSimplex, :_diagnostic_kernel)
        d = JSimplex.SimplexDiagnostics(kernel_timing=true)
        @test JSimplex._diagnostic_kernel(() -> 42, d, :ftran) == 42
        @test d.kernel_calls[:ftran] == 1
        @test d.kernel_nanoseconds[:ftran] >= 0
        @test_throws ErrorException JSimplex._diagnostic_kernel(() -> error("kernel failed"), d, :ftran)
        @test d.kernel_calls[:ftran] == 2
        @test JSimplex._diagnostic_kernel(() -> 7, nothing, :ftran) == 7
    end
end

@testset "Simplex diagnostics retain recent events and lifetime counts" begin
    @test isdefined(JSimplex, :SimplexDiagnostics)
    if isdefined(JSimplex, :SimplexDiagnostics)
        d = JSimplex.SimplexDiagnostics()
        @test JSimplex.event_count(d, :refactor_residual) == 0
        for _ in 1:100
            @test JSimplex.record_event!(d, :refactor_residual) === nothing
        end
        @test JSimplex.event_count(d, :refactor_residual) == 100
        @test length(d.events) == 64
        for _ in 1:3
            JSimplex.record_event!(d, :pivot_completed)
        end
        @test JSimplex.event_count(d, :pivot_completed) == 3
        @test JSimplex.event_count(d, :refactor_residual) == 100
        @test JSimplex.recent_events(d)[end-2:end] == fill(:pivot_completed, 3)
        @test count(==(:refactor_residual), JSimplex.recent_events(d)) == 61
        independent = JSimplex.SimplexDiagnostics()
        @test isempty(independent.events)
        @test JSimplex.event_count(independent, :pivot_completed) == 0
    end
end

@testset "Opt-in diagnostics preserve simplex results and count completed steps" begin
    @test isdefined(JSimplex, :_solve_diagnosed)
    if isdefined(JSimplex, :_solve_diagnosed)
        for T in (Float32, Float64, BigFloat, Rational{BigInt}), algorithm in (:dual, :primal)
            p = LinearProblem(JSimplex.sparse(T[1 1]), T[1, 2]; row_lower=T[1])
            options = SolverOptions(T; algorithm, verbose=false, presolve=false)
            reference = solve(p; options)
            d = JSimplex.SimplexDiagnostics()
            actual = JSimplex._solve_diagnosed(p, d; options)
            @test actual.status == reference.status == OPTIMAL
            @test actual.objective_value == reference.objective_value == one(T)
            @test actual.primal == reference.primal
            @test actual.statistics.iterations == reference.statistics.iterations
            @test JSimplex.event_count(d, :pivot_completed) +
                  JSimplex.event_count(d, :flip_completed) == actual.statistics.iterations
            @test JSimplex.event_count(d, :certification) > 0
        end
    end
end

# Normal event recording must remain allocation-free after warmup, including
# wraparound: allocating a new history or formatted message would fail this.
function diagnostics_record_allocations(d)
    JSimplex.record_event!(d, :pivot_completed)
    return @allocated for _ in 1:1000
        JSimplex.record_event!(d, :pivot_completed)
    end
end

if isdefined(JSimplex, :SimplexDiagnostics)
    @testset "Diagnostic observer failures do not become numerical statuses" begin
        if isdefined(JSimplex, :_solve_diagnosed)
            p = LinearProblem(JSimplex.sparse([1.0 1.0]), [1.0, 2.0]; row_lower=[1.0])
            for algorithm in (:dual, :primal)
                d = JSimplex.SimplexDiagnostics(observer=(_, _) -> throw(JSimplex.SingularException(1)))
                @test_throws Exception JSimplex._solve_diagnosed(p, d;
                    options=SolverOptions(; algorithm, presolve=false, verbose=false))
            end
        end
    end
    @testset "Simplex diagnostic event recording does not allocate" begin
        d = JSimplex.SimplexDiagnostics()
        diagnostics_record_allocations(d)
        @test diagnostics_record_allocations(d) == 0
    end
end
