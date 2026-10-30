using Test, JSimplex, SparseArrays

function ratio_overflow_workspace(T; reverse=false, finite_row=true, entering_bound=false)
    tiny=nextfloat(zero(T))
    sign=reverse ? -one(T) : one(T)
    a=finite_row ? T[tiny,1] : T[tiny]
    upper=finite_row ? T[3,2] : T[3]
    problem=LinearProblem(sparse(reshape(sign .* a,:,1)),T[-sign];
        row_upper=upper,
        column_lower=T[reverse ? (entering_bound ? -1 : -Inf) : 0],
        column_upper=T[reverse ? 0 : (entering_bound ? 1 : Inf)])
    options=SolverOptions(T;algorithm=:primal,verbose=false,presolve=false,scaling=:off)
    ws=JSimplex.initialize_workspace(problem,options)
    ws.basis.states[1]=reverse ? JSimplex.AT_UPPER : JSimplex.AT_LOWER
    JSimplex.recompute!(ws)
    return ws,sign,-sign .* a
end

@testset "A finite blocker wins over a positive overflowing ratio" begin
    for T in (Float32,Float64), reverse in (false,true)
        ws,direction,column=ratio_overflow_workspace(T;reverse)
        @test isinf(T(3)/abs(column[1]))
        @test JSimplex.primal_infeasibility(ws)==0
        @test JSimplex._primal_ratio(ws,1,direction,column)==(T(2),2,JSimplex.AT_UPPER)
        # Exercise the real basis solve and pivot, not only the ratio helper.
        @test isnothing(JSimplex._primal_iteration!(ws,()->false,ws.options.dual_tolerance))
        @test ws.iterations==1
        @test ws.primal[1]==direction*T(2)
        @test JSimplex._original_primal_feasible(ws.problem,ws.primal[1:1],ws.options.primal_tolerance)
    end
end

@testset "A finite entering bound wins over an overflowing basic ratio" begin
    for T in (Float32,Float64), reverse in (false,true)
        ws,direction,column=ratio_overflow_workspace(T;reverse,finite_row=false,entering_bound=true)
        @test JSimplex._primal_ratio(ws,1,direction,column)==(one(T),0,JSimplex.BASIC)
        @test isnothing(JSimplex._primal_iteration!(ws,()->false,ws.options.dual_tolerance))
        @test ws.primal[1]==direction
        @test JSimplex.primal_infeasibility(ws)==0
    end
end

@testset "Overflow alone does not certify an unbounded direction" begin
    for T in (Float32,Float64)
        ws,direction,column=ratio_overflow_workspace(T;finite_row=false)
        @test JSimplex._primal_ratio(ws,1,direction,column)==(nothing,-1,JSimplex.BASIC)
        @test JSimplex._primal_iteration!(ws,()->false,ws.options.dual_tolerance).status==NUMERICAL_ERROR
        @test ws.iterations==0
    end
end

@testset "Invalid ratios remain inconclusive" begin
    for T in (Float32,Float64), invalid in (:negative_overflow,:nan,:infinite_value,:overflowing_subtraction)
        ws,direction,column=ratio_overflow_workspace(T)
        index=ws.basis.basic_indices[1]
        if invalid==:negative_overflow
            ws.primal[index]=T(4) # Beyond the upper bound; tiny negative ratio divisor.
        elseif invalid==:nan
            column[1]=T(NaN)
            ws.lower[index]=JSimplex.Bound(zero(T))
        elseif invalid==:infinite_value
            ws.primal[index]=T(-Inf)
        else
            ws.upper[index]=JSimplex.Bound(floatmax(T))
            ws.primal[index]=-floatmax(T)
        end
        @test JSimplex._primal_ratio(ws,1,direction,column)==(nothing,-1,JSimplex.BASIC)
    end
end

@testset "BigFloat keeps finite blockers when an extreme ratio overflows" begin
    ws,direction,column=ratio_overflow_workspace(BigFloat)
    @test isinf(BigFloat(3)/abs(column[1]))
    @test JSimplex._primal_ratio(ws,1,direction,column)==(BigFloat(2),2,JSimplex.AT_UPPER)
    ws,direction,column=ratio_overflow_workspace(BigFloat;finite_row=false)
    @test JSimplex._primal_ratio(ws,1,direction,column)==(nothing,-1,JSimplex.BASIC)
end

@testset "An overflowing entering width does not hide a finite row bound" begin
    for T in (Float32,Float64)
        tiny=nextfloat(zero(T))
        p=LinearProblem(sparse(reshape(T[tiny,1],:,1)),T[-1];
            row_upper=T[3,0],column_lower=T[-floatmax(T)],column_upper=T[floatmax(T)])
        ws=JSimplex.initialize_workspace(p,SolverOptions(T;algorithm=:primal,verbose=false))
        @test ws.primal[1]==-floatmax(T)
        @test JSimplex.primal_infeasibility(ws)==0
        @test JSimplex._primal_ratio(ws,1,one(T),T[-tiny,-1])==
            (floatmax(T),2,JSimplex.AT_UPPER)
        # With only the remote first row, both finite bounds require steps
        # outside the scalar range. This must remain inconclusive, not unbounded.
        p=LinearProblem(sparse(reshape(T[tiny],:,1)),T[-1];
            row_upper=T[3],column_lower=T[-floatmax(T)],column_upper=T[floatmax(T)])
        ws=JSimplex.initialize_workspace(p,SolverOptions(T;algorithm=:primal,verbose=false))
        @test JSimplex._primal_ratio(ws,1,one(T),T[-tiny])==(nothing,-1,JSimplex.BASIC)
    end
end
