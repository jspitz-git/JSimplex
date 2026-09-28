using LinearAlgebra, SparseArrays

@testset "Auxiliary FTRAN preserves direction values while omitting preparation" begin
    available = isdefined(JSimplex, :_ordinary_forward_solve!)
    @test available
    if available
        for Factor in (JSimplex.ForrestTomlinFactorization,
                       JSimplex.SuhlSuhlFactorization, JSimplex.BartelsGolubFactorization),
            T in (Float32, Float64, BigFloat, Rational{BigInt})
            B = Matrix{T}(I, 4, 4)
            B[:, 1] = T[2, 1, 0, 1]
            f = Factor(B)
            entering = T[1, 3, 2, 1]
            direction = JSimplex.forward_solve(f, entering)
            expected = copy(direction)
            other = zeros(T, 4)
            for rhs in (T[2, 4, 1, 0], T[0, 3, 2, 1], T[1, 1, 1, 1])
                JSimplex._ordinary_forward_solve!(other, f, rhs)
                @test B * other ≈ rhs
                @test direction == expected
            end
            if T <: Union{Float32, Float64}
                @test !JSimplex._copy_prepared_spike!(f, direction)
                @test !JSimplex._copy_prepared_spike!(f, other)
            end
            JSimplex.replace_column!(f, direction, 2)
            B[:, 2] = entering
            JSimplex._ordinary_forward_solve!(other, f, ones(T, 4))
            @test B * other ≈ ones(T, 4)
            @test B' * JSimplex.transpose_solve(f, ones(T, 4)) ≈ ones(T, 4)
        end
    end
end

@testset "Auxiliary overwrite invalidates rounded-equal prepared output" begin
    available = isdefined(JSimplex, :_ordinary_forward_solve!)
    @test available
    if available
        for Factor in (JSimplex.ForrestTomlinFactorization,
                       JSimplex.SuhlSuhlFactorization, JSimplex.BartelsGolubFactorization)
            f = Factor(Matrix{Float64}(I, 2, 2))
            JSimplex.replace_column!(f, [2.0, 0.0], 1)
            d = JSimplex.forward_solve(f, [nextfloat(0.0), 1.0])
            @test d == [0.0, 1.0]
            @test JSimplex._copy_prepared_spike!(f, d)
            JSimplex._ordinary_forward_solve!(d, f, [0.0, 1.0])
            @test d == [0.0, 1.0]
            @test !JSimplex._copy_prepared_spike!(f, d)
            JSimplex.forward_solve!(d, f, [nextfloat(0.0), 1.0])
            @test JSimplex._copy_prepared_spike!(f, d)
            JSimplex._ordinary_forward_solve!(d, f, d)
            @test d == [0.0, 1.0]
            @test !JSimplex._copy_prepared_spike!(f, d)
            JSimplex._ordinary_forward_solve!(f.spike, f, [2.0, 3.0])
            @test f.spike == [1.0, 3.0]
            @test !JSimplex._copy_prepared_spike!(f, f.spike)
        end
    end
end

@testset "Legacy pipeline prepares only explicit entering columns" begin
    for update in (:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub)
        p = LinearProblem(spdiagm(0 => ones(4)), zeros(4); row_lower=zeros(4))
        options = SolverOptions(;simplex_strategy=:legacy, basis_update=update, verbose=false)
        ws = JSimplex.initialize_workspace(p, options)
        d, other = ws.scratch.row_solution, ws.scratch.tau
        rhs = JSimplex._pipeline_column_rhs!(ws, 1)
        JSimplex._pipeline_basis_solve!(d, ws, rhs; prepare_update=true)
        expected = copy(d)
        for i in 2:4
            rhs = JSimplex._pipeline_column_rhs!(ws, i)
            JSimplex._pipeline_basis_solve!(other, ws, rhs; operation=:weight_ftran)
        end
        @test d == expected
        if update != :pfi
            @test !JSimplex._copy_prepared_spike!(ws.factorization, d)
            @test !JSimplex._copy_prepared_spike!(ws.factorization, other)
            JSimplex._pipeline_basis_solve!(d, ws, rhs)
            @test !JSimplex._copy_prepared_spike!(ws.factorization, d)
        end
    end
end

@testset "Legacy residual corrections do not prepare an update" begin
    for update in (:forrest_tomlin, :suhl_suhl, :bartels_golub)
        p=LinearProblem(sparse([1.0 0.0;0.0 1.0]),[1.0,10.0];row_lower=[1.0,-Inf])
        ws=JSimplex.initialize_workspace(p,SolverOptions(;basis_update=update,verbose=false))
        ws.factorization.base=JSimplex._factorize_basis(sparse([-1.0 0.0;1e-5 -1.0]))
        d=JSimplex.forward_solve(ws.factorization,[1.0,0.0])
        ws.scratch.tableau_row[1]=-1.0
        @test JSimplex._try_native_dual_correction!(ws,d,1,1,()->false)
        @test d ≈ [-1.0,0.0]
        @test !JSimplex._copy_prepared_spike!(ws.factorization,ws.scratch.pivot_quality_cache.correction)
    end
end

@testset "Disabled hypersparsity preserves adaptive preparation" begin
    for update in (:forrest_tomlin, :suhl_suhl, :bartels_golub)
        p=LinearProblem(spdiagm(0=>ones(4)),zeros(4);row_lower=zeros(4))
        options=SolverOptions(;basis_update=update,simplex_strategy=:adaptive,verbose=false)
        policy=JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,hypersparse=false)
        ws=JSimplex.initialize_workspace(p,options;
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
        rhs=JSimplex._pipeline_column_rhs!(ws,1)
        d=ws.scratch.row_solution
        JSimplex._pipeline_basis_solve!(d,ws,rhs;operation=:weight_ftran)
        @test JSimplex._copy_prepared_spike!(ws.factorization,d)
    end
end
