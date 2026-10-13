@testset "BFRT subtraction does not negate a fixed-width minimum" begin
    T = Rational{Int64}
    for buffer in (T[-1],JSimplex.IndexedVector{T}(1))
        JSimplex._set_pipeline_rhs!(buffer,1,T(-1))
        JSimplex._subtract_pipeline_rhs!(buffer,1,T(typemin(Int64)))
        @test JSimplex._pipeline_rhs_values(buffer) == T[typemax(Int64)]
    end
    setprecision(BigFloat,256) do
        alpha = one(BigFloat)+BigFloat(2)^(-120)
        expected = alpha-one(BigFloat)
        buffer = JSimplex.IndexedVector{BigFloat}(1)
        JSimplex.set_entry!(buffer,1,alpha)
        setprecision(BigFloat,24) do
            JSimplex._subtract_pipeline_rhs!(buffer,1,one(BigFloat))
        end
        @test buffer.values[1] == expected
    end
end

@testset "Sparse weight coefficients retain stored BigFloat precision" begin
    setprecision(BigFloat,256) do
        ws = pipeline_workspace(BigFloat)
        rhs = JSimplex._pipeline_unit_rhs!(ws,3)
        alpha = one(BigFloat)+BigFloat(2)^(-120)
        JSimplex._pipeline_add!(ws,rhs,3,alpha-one(BigFloat))
        JSimplex._pipeline_basis_solve!(ws.scratch.row_solution,ws,rhs;kernel_mode=:sparse)
        expected = -alpha/2
        setprecision(BigFloat,24) do
            h = JSimplex._pipeline_weight_rhs!(ws,7,BigFloat(2))
            @test h[3] == expected
            @test precision(BigFloat) == 24
        end
    end
end
