using Profile
@testset "Optimality certification avoids concatenation scratch" begin
    problem = LinearProblem(JSimplex.SparseArrays.spzeros(Float64, 0, 1024), ones(1024))
    workspace = JSimplex.initialize_workspace(problem, SolverOptions(verbose=false))
    primal = zeros(1024)
    dual = Float64[]
    @test JSimplex._original_optimality_certified(workspace, primal)
    JSimplex._original_reduced_cost_bounds(problem, dual)
    @test (@allocated JSimplex._original_optimality_certified(workspace, primal)) <= 25_000
    @test (@allocated JSimplex._original_reduced_cost_bounds(problem, dual)) <= 20_000
end

@testset "Reduced-cost intervals own their arrays and retain slack values" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(JSimplex.SparseArrays.sparse(T[2 -1; 0 3]), T[4, 5])
        dual = T[1, -2]
        lower, upper = @inferred JSimplex._original_reduced_cost_bounds(problem, dual)
        @test lower == T[2, 12, 1, -2]
        @test upper == T[2, 12, 1, -2]
        lower[3] = T(99)
        upper[4] = T(-99)
        @test upper[3] == T(1)
        @test lower[4] == T(-2)
        @test dual == T[1, -2]
        @test problem.objective == T[4, 5]

        empty_problem = LinearProblem(JSimplex.SparseArrays.spzeros(T, 0, 0), T[])
        empty_workspace = JSimplex.initialize_workspace(empty_problem, SolverOptions(T;verbose=false))
        @test JSimplex._original_optimality_certified(empty_workspace, T[])
        @test JSimplex._original_reduced_cost_bounds(empty_problem, T[]) == (T[], T[])
    end
end

@testset "Certificate reads original basic costs and actual row values" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(JSimplex.SparseArrays.sparse(reshape(T[2, 1], 2, 1)), T[4];
            row_lower=[T(2), nothing], row_upper=[nothing, T(3)])
        workspace = JSimplex.initialize_workspace(problem, SolverOptions(T;verbose=false))
        workspace.basis = JSimplex.Basis([1, 3], [JSimplex.BASIC, JSimplex.AT_LOWER, JSimplex.BASIC])
        JSimplex.recompute!(workspace;refactorize=true)
        fill!(workspace.costs, T(99))
        @test JSimplex._original_optimality_certified(workspace, T[1])
        @test !JSimplex._original_optimality_certified(workspace, T[2])
        @test workspace.costs == T[99, 99, 99]
        workspace.basis.basic_indices[2] = 4
        @test_throws BoundsError JSimplex._original_optimality_certified(workspace, T[1])

        upper_problem = LinearProblem(JSimplex.SparseArrays.sparse(T[2 0; 0 3]), T[4, -6];
            row_lower=[T(2), nothing], row_upper=[nothing, T(6)])
        upper_workspace = JSimplex.initialize_workspace(upper_problem, SolverOptions(T;verbose=false))
        upper_workspace.basis = JSimplex.Basis([1, 2],
            [JSimplex.BASIC, JSimplex.BASIC, JSimplex.AT_LOWER, JSimplex.AT_UPPER])
        JSimplex.recompute!(upper_workspace;refactorize=true)
        @test JSimplex._original_optimality_certified(upper_workspace, T[1, 2])
        @test !JSimplex._original_optimality_certified(upper_workspace, T[1, 1])
    end
end

@testset "Reduced-cost slack intervals preserve stored BigFloat precision" begin
    problem, dual = setprecision(BigFloat, 512) do
        LinearProblem(JSimplex.SparseArrays.spzeros(BigFloat, 1, 0), BigFloat[]),
        [BigFloat(1) + BigFloat(2)^(-300)]
    end
    setprecision(BigFloat, 64) do
        lower, upper = JSimplex._original_reduced_cost_bounds(problem, dual)
        @test isequal(lower, dual) && isequal(upper, dual)
        @test precision(only(lower)) == precision(only(upper)) == 512
    end
end

@testset "Exact row fallback does not allocate per matrix coefficient" begin
    for T in (Float32,Float64)
        columns=10_000
        A=JSimplex.SparseArrays.sparse(ones(Int,columns),collect(1:columns),ones(T,columns),1,columns)
        problem=LinearProblem(A,zeros(T,columns);row_lower=T[1250],row_upper=T[1250])
        primal=fill(T(0.125),columns)
        rows=[1]
        @test JSimplex._exact_primal_rows_feasible(problem,primal,zero(T),rows)
        # Storage should scale with the checked rows, not millions of temporary
        # BigInts as more coefficients enter the same exact dot product.
        @test (@allocated JSimplex._exact_primal_rows_feasible(problem,primal,zero(T),rows)) < 100_000
    end
end

@testset "Conclusive native row checks do not allocate arbitrary-precision numbers" begin
    # The large terms cancel exactly; naive intervals are wider than tolerance,
    # but compensated native arithmetic can certify the stored activity 1.
    for T in (Float32,Float64)
        big=T(2)^(T===Float32 ? 24 : 53)
        p=LinearProblem(JSimplex.SparseArrays.sparse(reshape(T[big,1,-big],1,3)),zeros(T,3);
            row_lower=T[1],row_upper=T[1])
        x=ones(T,3);rows=[1];tol=T(1e-7)
        @test JSimplex._refined_primal_rows_feasible(p,x,tol,rows)
        Profile.Allocs.clear()
        Profile.Allocs.@profile sample_rate=1.0 JSimplex._refined_primal_rows_feasible(p,x,tol,rows)
        allocations=Profile.Allocs.fetch().allocs
        @test all(a->a.type!==BigInt,allocations)
        Profile.Allocs.clear()
    end
end
