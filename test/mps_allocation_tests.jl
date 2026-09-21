@testset "MPS allocation budgets" begin
    path = joinpath(@__DIR__, "fixtures", "solver", "netlib", "adlittle.mps")
    for format in (:auto, :fixed)
        read_mps(path; format)
        @test (@allocated read_mps(path; format)) <= 500_000
        JSimplex._parse_mps_file(path; format)
        @test (@allocated JSimplex._parse_mps_file(path; format)) <= 350_000
    end
end

@testset "MPS names and comments survive temporary token views" begin
    text = "NAME VIEWS\nROWS\n N COST\n L r\$one\nCOLUMNS\n x\$one COST 1.25 r\$one 2d0 \$ ignore 99\nRHS\n rhs r\$one 6\nBOUNDS\n UP b x\$one 4\nENDATA\n"
    for T in (Float32, Float64, BigFloat, Rational{Int}, Rational{BigInt}), format in (:free, :auto)
        records = JSimplex._parse_mps(IOBuffer(text), "views.mps", T; format)
        problem = JSimplex._build_mps(records)
        @test problem.column_names == ["x\$one"]
        @test problem.row_names == ["r\$one"]
        @test problem.objective == T[5//4]
        @test problem.A[1, 1] == T(2)
        @test bound_value(only(problem.row_upper)) == T(6)
        @test bound_value(only(problem.column_upper)) == T(4)
        empty!(records.coefficients)
        empty!(records.row_order)
        empty!(records.column_order)
        GC.gc()
        @test problem.column_names == ["x\$one"]
        @test problem.row_names == ["r\$one"]
    end
end
