@testset "Checkpoint recovery replaces sparse caches at stored precision" begin
    setprecision(BigFloat,384) do
        delta = BigFloat(2)^(-180)
        p = LinearProblem(sparse(BigFloat[1 1;1 1+delta]),zeros(BigFloat,2);
            row_lower=BigFloat[1,1+delta])
        policy = JSimplex.NumericalPolicy(BigFloat;hypersparse=true)
        ws = JSimplex.initialize_workspace(p,SolverOptions(BigFloat;verbose=false,
            basis_refactorization=:markowitz);
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
        ws.basis = JSimplex.Basis([1,2],
            [JSimplex.BASIC,JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER])
        JSimplex.recompute!(ws;refactorize=true)
        rhs = JSimplex._pipeline_unit_rhs!(ws,1)
        JSimplex._pipeline_basis_solve!(ws.scratch.rho,ws,rhs;transposed=true,kernel_mode=:sparse)
        old_cache = ws.factorization.sparse
        checkpoint = JSimplex.checkpoint_basis(ws)
        setprecision(BigFloat,96) do
            @test JSimplex.restore_checkpoint!(ws,checkpoint,()->false)
            @test precision(BigFloat) == 96
        end
        @test ws.factorization.sparse !== old_cache
        @test ws.primal[1:2] == BigFloat[0,1]
        @test JSimplex._recomputed_basis_reliable(ws)
        @test Set(JSimplex._pipeline_vector!(ws,ws.scratch.rho).indices) ==
            Set(findall(!iszero,ws.scratch.rho))
    end
end

@testset "Numerical overflow discards a partially computed pipeline candidate" begin
    ws = pipeline_workspace()
    before = (copy(ws.primal),copy(ws.basis.basic_indices),copy(ws.costs))
    JSimplex.refactorize!(ws.factorization,spdiagm(0=>fill(1e-200,32)))
    @test_throws JSimplex._UnreliableBasisSolve JSimplex._transactional_simplex_step!(ws,()->false) do candidate,stop
        rhs = JSimplex._pipeline_unit_rhs!(candidate,1)
        JSimplex._pipeline_add!(candidate,rhs,1,1e200)
        JSimplex._pipeline_basis_solve!(candidate.scratch.row_solution,candidate,rhs;kernel_mode=:sparse)
    end
    @test before == (ws.primal,ws.basis.basic_indices,ws.costs)
    @test ws.iterations == 0
    JSimplex.refactorize!(ws.factorization,JSimplex.basis_matrix(ws))
    rhs = JSimplex._pipeline_unit_rhs!(ws,7)
    JSimplex._pipeline_basis_solve!(ws.scratch.row_solution,ws,rhs;kernel_mode=:sparse)
    @test ws.scratch.row_solution == -rhs
    @test JSimplex._pipeline_vector!(ws,ws.scratch.row_solution).indices == [7]
end

function pipeline_repeated_calls!(ws,mode,repetitions)
    for _ in 1:repetitions
        rhs = JSimplex._pipeline_unit_rhs!(ws,1)
        JSimplex._pipeline_basis_solve!(ws.scratch.rho,ws,rhs;transposed=true,kernel_mode=mode)
        JSimplex._pipeline_price!(ws.scratch.tableau_row,ws,ws.scratch.rho;kernel_mode=mode)
    end
    return nothing
end

@testset "Warm sparse pipeline reuses storage across operations" begin
    ws = pipeline_workspace(;n=1024)
    for mode in (:sparse,:dense,:auto)
        pipeline_repeated_calls!(ws,mode,64)
        used = @allocated pipeline_repeated_calls!(ws,mode,64)
        # A single full Vector{Float64} copy would already exceed this budget.
        @test used <= 4096
        @test ws.scratch.rho[1] == -1
        @test ws.scratch.tableau_row[1] == -1
        @test ws.scratch.tableau_row[1025] == 1
    end
end
