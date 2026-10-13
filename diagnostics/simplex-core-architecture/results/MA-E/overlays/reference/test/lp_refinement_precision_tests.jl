using Test, JSimplex, SparseArrays

@testset "LP correction scaling interface" begin
    @test isdefined(JSimplex, :_lp_correction_scales)
end

if isdefined(JSimplex, :_lp_correction_scales)
    @testset "Correction scales amplify residuals within working representability" begin
        for T in (Float32, Float64)
            delta = T === Float32 ? T(2)^(-16) : T(2)^(-40)
            p = LinearProblem(sparse(reshape(T[1],1,1)), T[0];
                column_lower=T[0], column_upper=[nothing], row_lower=T[1], row_upper=T[1])
            ws = JSimplex.initialize_workspace(p, SolverOptions(T; verbose=false))
            r = JSimplex._lp_residuals(ws, T[1-delta,1], T[delta])
            sp, sd = JSimplex._lp_correction_scales(ws, r)
            correction, _ = JSimplex.build_correction_problem(ws,r,sp,sd)
            @test sp == inv(BigFloat(delta)) && sd == inv(BigFloat(delta))
            @test bound_value.(correction.row_lower) == T[1]
            @test correction.objective == T[-1,1]
            @test !isfinite(correction.column_upper[1])
            @test eltype(correction.A) === T
            bounded = LinearProblem(p.A,p.objective; column_lower=T[0],
                column_upper=T[floatmax(T)], row_lower=T[1], row_upper=T[1])
            ws2 = JSimplex.initialize_workspace(bounded,ws.options)
            r2 = JSimplex._lp_residuals(ws2,T[1-delta,1],T[delta])
            sp2,sd2 = JSimplex._lp_correction_scales(ws2,r2)
            correction2,_ = JSimplex.build_correction_problem(ws2,r2,sp2,sd2)
            @test sp2 <= 1 && sd2 == sd
            @test isfinite(bound_value(correction2.column_upper[1]))
            @test !iszero(bound_value(correction2.row_lower[1]))
            tiny = BigFloat(nextfloat(zero(T)))/4
            # Construct the tiny difference without ambient rounding erasing it.
            tiny_r = setprecision(BigFloat,2048) do
                JSimplex._lp_residuals(ws,[BigFloat(1)-tiny,BigFloat(1)],BigFloat[0];bits=2048)
            end
            @test_throws ArgumentError JSimplex.build_correction_problem(ws,tiny_r,1,1)
            @test_throws ArgumentError JSimplex.build_correction_problem(ws,r,0,1)
            @test_throws ArgumentError JSimplex.build_correction_problem(ws,r,Inf,1)
            @test_throws DimensionMismatch JSimplex._lp_residuals(ws,T[1],T[0])
            @test_throws ArgumentError JSimplex._lp_residuals(ws,T[Inf,1],T[0])
        end
    end
    @testset "Correction residuals preserve wider stored binary inputs" begin
        ws,values,multipliers = setprecision(BigFloat,512) do
            a = BigFloat(1)+BigFloat(2)^(-200)
            p = LinearProblem(sparse(reshape([a],1,1)),BigFloat[1];
                column_lower=BigFloat[0],row_lower=BigFloat[1],row_upper=BigFloat[1])
            JSimplex.initialize_workspace(p,SolverOptions(BigFloat;verbose=false)),
                BigFloat[1,1],BigFloat[1]
        end
        setprecision(BigFloat,64) do
            r = JSimplex._lp_residuals(ws,values,multipliers)
            @test Rational{BigInt}(only(r.primal)) == -1//(big(1)<<200)
            @test Rational{BigInt}(r.dual[1]) == -1//(big(1)<<200)
            correction,_ = JSimplex.build_correction_problem(ws,r,BigFloat(2)^200,1)
            @test bound_value.(correction.row_lower) == [-1]
            @test correction.A.nzval[1] == ws.problem.A.nzval[1]
            # Julia's BigFloat-to-Rational conversion itself uses ambient arithmetic.
            exact_coefficient = setprecision(BigFloat,512) do
                Rational{BigInt}(correction.A.nzval[1])
            end
            @test exact_coefficient == 1+1//(big(1)<<200)
            @test precision(correction.A[1,1]) >= 512
            @test precision(BigFloat) == 64
        end
    end
end
