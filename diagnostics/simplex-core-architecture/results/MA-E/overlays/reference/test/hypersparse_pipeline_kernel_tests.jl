@testset "Pipeline solve and price preserve owned support across kernels" begin
    for T in (Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt}),
        method in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub),backend in (:native,:markowitz)
        ws = pipeline_workspace(T;basis_update=method,backend)
        cache = JSimplex._hypersparse_workspace!(ws)
        for mode in (:sparse,:dense,:auto), transposed in (false,true)
            rhs = JSimplex._pipeline_unit_rhs!(ws,3)
            out = transposed ? ws.scratch.rho : ws.scratch.row_solution
            returned = JSimplex._pipeline_basis_solve!(out,ws,rhs;transposed,kernel_mode=mode)
            @test returned === out
            @test out == -T[i==3 for i in 1:32]
            indexed = JSimplex._pipeline_vector!(ws,out)
            @test indexed.indices == [3]
            before = cache.support_rebuilds
            JSimplex._pipeline_price!(ws.scratch.tableau_row,ws,out;kernel_mode=mode)
            expected = zeros(T,64); expected[3] = -one(T); expected[35] = one(T)
            @test ws.scratch.tableau_row == expected
            @test Set(JSimplex._pipeline_vector!(ws,ws.scratch.tableau_row).indices) == Set([3,35])
            if mode == :sparse
                @test cache.support_rebuilds == before
            end
            @test rhs == T[i==3 for i in 1:32]
        end
        for mode in (:sparse,:dense)
            rhs = JSimplex._pipeline_unit_rhs!(ws,4)
            JSimplex._pipeline_basis_solve!(rhs,ws,rhs;kernel_mode=mode)
            @test rhs == -T[i==4 for i in 1:32]
            @test JSimplex._pipeline_vector!(ws,rhs).indices == [4]
        end
    end
end

@testset "Pipeline repairs support after dense writes and empty solves" begin
    ws = pipeline_workspace()
    cache = JSimplex._hypersparse_workspace!(ws)
    rhs = JSimplex._pipeline_unit_rhs!(ws,2)
    out = ws.scratch.rho
    JSimplex._pipeline_basis_solve!(out,ws,rhs;kernel_mode=:sparse)
    out[9] = 3.0
    JSimplex._pipeline_changed!(ws,out)
    JSimplex._pipeline_price!(ws.scratch.tableau_row,ws,out;kernel_mode=:sparse)
    @test ws.scratch.tableau_row[9] == 3.0
    @test ws.scratch.tableau_row[32+9] == -3.0
    @test Set(JSimplex._pipeline_vector!(ws,ws.scratch.tableau_row).indices) == Set([2,9,34,41])
    rhs = JSimplex._pipeline_unit_rhs!(ws,2)
    JSimplex._pipeline_add!(ws,rhs,2,-1.0)
    JSimplex._pipeline_basis_solve!(out,ws,rhs)
    @test all(iszero,out)
    @test isempty(JSimplex._pipeline_vector!(ws,out).indices)
    external = zeros(32); external[8] = 2.0
    JSimplex._pipeline_basis_solve!(out,ws,external;kernel_mode=:sparse)
    @test out == -external
    @test JSimplex._pipeline_vector!(ws,out).indices == [8]
end

@testset "Every pipeline branch retains stored BigFloat precision" begin
    setprecision(BigFloat,256) do
        alpha = one(BigFloat)+BigFloat(2)^(-120)
        expected_direction = -alpha
        for backend in (:native,:markowitz),mode in (:sparse,:dense,:auto)
            ws = pipeline_workspace(BigFloat;backend)
            ws.problem.A.nzval[1] = alpha
            expected = zeros(BigFloat,64); expected[1] = -alpha^2; expected[33] = alpha
            setprecision(BigFloat,24) do
                rhs = JSimplex._pipeline_column_rhs!(ws,1)
                out = ws.scratch.row_solution
                JSimplex._pipeline_basis_solve!(out,ws,rhs;kernel_mode=mode)
                @test out[1] == expected_direction
                JSimplex._pipeline_price!(ws.scratch.tableau_row,ws,out;kernel_mode=mode)
                @test ws.scratch.tableau_row == expected
                @test precision(BigFloat) == 24
            end
        end
    end
end
