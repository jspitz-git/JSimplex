using SparseArrays

@testset "Basic shared bound shifts match exact interval translation" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), coefficient in (-3,3), value in (-2,0,2), bounds in ((-7,-7),(0,0),(5,5),(-7,5),(nothing,5),(-7,nothing),(nothing,nothing)), cached in (false,true)
        lo,hi=bounds;cast(x)=isnothing(x) ? nothing : T(x)
        problem=LinearProblem(sparse(reshape(T[coefficient,5],1,2)),T[2,3];objective_constant=T(7),
            row_lower=[cast(lo)],row_upper=[cast(hi)],column_lower=[T(value),nothing],column_upper=[T(value),nothing])
        original=deepcopy(problem);selections=[JSimplex._elimination_value(problem,i) for i in 1:2];saved=deepcopy(selections)
        result=cached ? JSimplex._presolve_basic(problem;selections) : JSimplex._presolve_basic(problem)
        shift=big(coefficient)*value//big(1)
        translated(x)=isnothing(x) ? Bound{T}(nothing) : Bound(T(x-shift))
        @test result.problem.A==reshape(T[5],1,1)
        @test result.problem.row_lower==[translated(lo)]
        @test result.problem.row_upper==[translated(hi)]
        @test result.problem.objective==T[3] && result.problem.objective_constant==7+2value
        @test only(result.postsolve_stack).columns==[2]
        @test JSimplex.postsolve_primal(result,T[1])==T[value,1]
        basis=JSimplex.Basis([2],[JSimplex.FREE_NONBASIC,JSimplex.BASIC]);restored=JSimplex.restore_basis(result,basis)
        @test restored.basic_indices==[3] && restored.states==[JSimplex.AT_LOWER,JSimplex.FREE_NONBASIC,JSimplex.BASIC]
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
        @test isequal(selections,saved)
    end
end

@testset "Basic zero shifts retain distinct bound representations" begin
    for T in (Float32,Float64)
        problem=LinearProblem(sparse(reshape(T[6,5],1,2)),T[0,2];row_lower=T[-0.0],row_upper=T[0.0],
            column_lower=[T(0),nothing],column_upper=[T(0),nothing])
        original=deepcopy(problem);result=JSimplex._presolve_basic(problem)
        @test isequal(bound_value(only(result.problem.row_lower)),T(-0.0))
        @test isequal(bound_value(only(result.problem.row_upper)),T(0.0))
        @test isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
    problem=setprecision(BigFloat,256) do
        LinearProblem(sparse(reshape(BigFloat[6,5],1,2)),BigFloat[0,2];row_lower=BigFloat[20],row_upper=BigFloat[20],
            column_lower=[BigFloat(0),nothing],column_upper=[BigFloat(0),nothing])
    end
    problem.row_lower[1]=Bound(setprecision(()->BigFloat(20),BigFloat,128))
    for ambient in (32,64,256)
        setprecision(BigFloat,ambient) do
            result=JSimplex._presolve_basic(problem)
            @test precision(bound_value(only(result.problem.row_lower)))==128
            @test precision(bound_value(only(result.problem.row_upper)))==256
            @test precision(bound_value(problem.row_lower[1]))==128 && precision(bound_value(problem.row_upper[1]))==256
        end
    end
end

@testset "Basic shared shifted bounds preserve exact representation gates" begin
    for value in (-2,2), kind in (:equal_inexact,:unequal_neighbor,:equal_exact), ambient in (32,64,256)
        problem,expected_lower,expected_upper=setprecision(BigFloat,256) do
            tiny=BigFloat(2)^(-200)
            low=kind==:equal_inexact ? one(BigFloat)+tiny : BigFloat(20)
            high=kind==:unequal_neighbor ? low+tiny : low
            p=LinearProblem(sparse(reshape(BigFloat[6,5],1,2)),BigFloat[0,2];objective_constant=BigFloat(7),
                row_lower=[low],row_upper=[high],column_lower=[BigFloat(value),nothing],column_upper=[BigFloat(value),nothing])
            p,low-6value,high-6value
        end
        original=deepcopy(problem)
        setprecision(BigFloat,ambient) do
            result=JSimplex._presolve_basic(problem);accepted=ambient==256 || kind==:equal_exact
            @test isempty(result.postsolve_stack)==!accepted
            @test size(result.problem.A)==(accepted ? (1,1) : (1,2))
            @test result.problem.row_lower==(accepted ? [Bound(expected_lower)] : original.row_lower) && result.problem.row_upper==(accepted ? [Bound(expected_upper)] : original.row_upper)
            @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
        end
    end
    for T in (Float32,Float64)
        problem=LinearProblem(sparse(reshape(T[2,5],1,2)),T[0,2];row_lower=T[floatmax(T)],row_upper=T[floatmax(T)],
            column_lower=[-floatmax(T),nothing],column_upper=[-floatmax(T),nothing])
        original=deepcopy(problem);result=JSimplex._presolve_basic(problem)
        @test result.problem===problem
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Basic shared shifts accumulate in private equality bounds" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), cached in (false,true)
        problem=LinearProblem(sparse(T[2 3 1;1 -1 2]),T[2,3,4];objective_constant=T(7),
            row_lower=T[20,10],row_upper=T[20,10],column_lower=[T(2),T(-1),nothing],column_upper=[T(2),T(-1),nothing])
        original=deepcopy(problem);selections=[JSimplex._elimination_value(problem,i) for i in 1:3]
        result=cached ? JSimplex._presolve_basic(problem;selections) : JSimplex._presolve_basic(problem)
        @test result.problem.A==reshape(T[1,2],2,1)
        @test bound_value.(result.problem.row_lower)==T[19,7] && bound_value.(result.problem.row_upper)==T[19,7]
        @test result.problem.objective==T[4] && result.problem.objective_constant==8
        @test only(result.postsolve_stack).columns==[3]
        @test JSimplex.postsolve_primal(result,T[3])==T[2,-1,3]
        basis=JSimplex.Basis([2,3],[JSimplex.FREE_NONBASIC,JSimplex.BASIC,JSimplex.BASIC])
        @test JSimplex.restore_basis(result,basis).basic_indices==[4,5]
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Basic presolve shares nonzero shifts of equal bounds" begin
function basic_shared_shifted_bounds_probe(kind; count=128, T=Float64)
    value=kind==:negative ? T(-2) : kind==:zero_shift ? zero(T) : T(2)
    upper=kind==:negative ? T(16) : kind==:cancelled ? T(12) : kind==:zero_bound ? zero(T) : T(20)
    lower=kind==:unequal ? T(-20) : upper
    problem=LinearProblem(sparse(hcat(fill(T(6),count),fill(T(5),count))),T[0,2];objective_constant=T(7),
        row_lower=fill(lower,count),row_upper=fill(upper,count),
        column_lower=[value,nothing],column_upper=[value,nothing])
    return problem,JSimplex._presolve_basic
end
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive,:negative,:cancelled,:zero_bound,:unequal,:zero_shift)
        count=4;problem,pass=basic_shared_shifted_bounds_probe(kind;count,T)
        original=deepcopy(problem);result=pass(problem);value=bound_value(problem.column_lower[1]);shift=6value
        @test result.problem.A==fill(T(5),count,1)
        @test result.problem.row_lower==fill(Bound(bound_value(problem.row_lower[1])-shift),count)
        @test result.problem.row_upper==fill(Bound(bound_value(problem.row_upper[1])-shift),count)
        @test result.problem.objective==T[2] && result.problem.objective_constant==7
        @test only(result.postsolve_stack).columns==[2]
        primal=T[1];restored=JSimplex.postsolve_primal(result,primal)
        @test restored==T[value,1]
        @test problem.objective_constant+sum(problem.objective.*restored)==result.problem.objective_constant+sum(result.problem.objective.*primal)
        for state in (JSimplex.AT_LOWER,JSimplex.AT_UPPER)
            basis=JSimplex.Basis(collect(2:count+1),[state;fill(JSimplex.BASIC,count)]);restored_basis=JSimplex.restore_basis(result,basis)
            @test restored_basis.basic_indices==collect(3:count+2)
            @test restored_basis.states[1:2]==[JSimplex.AT_LOWER,state]
        end
        result.problem.objective[1]+=one(T);result.problem.A.nzval[1]+=one(T);result.problem.row_upper[1]=Bound(T(20))
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective)
        @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
        @test isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
    for (kind,limit) in ((:positive,10476),(:negative,10476),(:cancelled,8940),(:zero_bound,6124),(:unequal,11540),(:zero_shift,145))
        problem,pass=basic_shared_shifted_bounds_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
