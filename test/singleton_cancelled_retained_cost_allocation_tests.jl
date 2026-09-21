using SparseArrays

@testset "Singleton: Cancelled retained costs preserve objectives and projections" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), ratio in (-3,-1,-1//2,1//2,1,3), term in (-3,-1,1,3), implied in (false,true)
        problem=LinearProblem(sparse(T[2 term;0 1]),T[2ratio,ratio*term];objective_constant=T(7),
            row_lower=T[4,-100],row_upper=T[4,100],
            column_lower=[implied ? nothing : T(1),nothing],column_upper=[implied ? nothing : T(3),nothing])
        original=deepcopy(problem)
        result=JSimplex.aggregate_singleton_equalities(problem)
        @test size(result.problem.A)==(2,1)
        @test isequal(only(result.problem.objective),zero(T))
        @test result.problem.objective_constant==T(7+4ratio)
        @test result.problem.A[end,1]==T(1)
        @test JSimplex.bound_value(result.problem.row_lower[end])==-100 && JSimplex.bound_value(result.problem.row_upper[end])==100
        x=JSimplex.postsolve_primal(result,T[2])
        @test x==T[2-term,2]
        @test sum(problem.objective.*x)+problem.objective_constant==result.problem.objective_constant
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Singleton: Cost cancellation uses the currently committed objective" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), ratios in ((1,1),(1,-1),(-1,3),(0,1)), old in (0,3,6,9)
        r1,r2=ratios
        problem=LinearProblem(sparse(T[2 0 3;0 2 3;0 0 5]),T[2r1,2r2,old];objective_constant=T(7),
            row_lower=[T(4),T(4),nothing],row_upper=T[4,4,20],column_lower=fill(nothing,3),column_upper=fill(nothing,3))
        original=deepcopy(problem)
        result=JSimplex.aggregate_singleton_equalities(problem)
        @test size(result.problem.A)==(3,1)
        @test result.problem.objective==T[old-3r1-3r2]
        @test result.problem.objective_constant==T(7+4r1+4r2)
        @test JSimplex.bound_value(result.problem.row_upper[end])==T(20)
        @test JSimplex.postsolve_primal(result,T[2])==T[-1,-1,2]
        @test isequal(problem.objective,original.objective) && isequal(problem.A.nzval,original.A.nzval)
    end
end

@testset "Singleton: High-precision costs cancel exactly without losing tiny residuals" begin
    for side in (:ratio,:term), mode in (:cancel,:tail,:inexact), ambient in (32,64,256), direction in (-1,1)
        problem=setprecision(BigFloat,256) do
            epsilon=BigFloat(2)^(-200)
            value=direction*(BigFloat(3)+epsilon)
            ratio,term=side==:ratio ? (value,BigFloat(1)) : (BigFloat(1),value)
            product=ratio*term
            old=mode==:cancel ? product : mode==:tail ? product-direction*2epsilon : product+BigFloat(2)+epsilon
            A=sparse(BigFloat[2 term;0 1])
            LinearProblem(A,BigFloat[2ratio,old];objective_constant=BigFloat(7),
                row_lower=[BigFloat(0),nothing],row_upper=[BigFloat(0),nothing],
                column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        saved_cost=JSimplex._exact_rational.(problem.objective)
        saved_matrix=JSimplex._exact_rational.(problem.A.nzval)
        expected=saved_cost[2]-saved_cost[1]/2*JSimplex._exact_rational(problem.A[1,2])
        setprecision(BigFloat,ambient) do
            result=JSimplex.aggregate_singleton_equalities(problem)
            if mode==:inexact && ambient<256
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            else
                @test size(result.problem.A)==(2,1)
                @test JSimplex._exact_rational(only(result.problem.objective))==expected
                @test precision(only(result.problem.objective))==ambient
                @test mode==:cancel ? !signbit(only(result.problem.objective)) : !iszero(only(result.problem.objective))
            end
            @test JSimplex._exact_rational.(problem.objective)==saved_cost
            @test JSimplex._exact_rational.(problem.A.nzval)==saved_matrix
        end
    end
end

@testset "Singleton: Adjacent floating costs are not treated as cancellation" begin
    for T in (Float32,Float64), ratio in (-3,-1,1,3), direction in (-1,1)
        product=T(3ratio);old=direction>0 ? nextfloat(product) : prevfloat(product)
        problem=LinearProblem(sparse(T[2 3;0 1]),T[2ratio,old];objective_constant=T(7),
            row_lower=[T(0),nothing],row_upper=[T(0),nothing],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        result=JSimplex.aggregate_singleton_equalities(problem)
        @test size(result.problem.A)==(2,1)
        @test only(result.problem.objective)==old-product
        @test !iszero(only(result.problem.objective))
        @test problem.objective==T[2ratio,old]
    end
end

@testset "Singleton: Non-dyadic rational costs cancel to canonical zero" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), direction in (-1,1), side in (:ratio,:term)
        value=T((BigInt(1)<<300)+1,BigInt(den))
        ratio,term=side==:ratio ? (value,T(direction)) : (T(direction),value)
        problem=LinearProblem(sparse(T[2 term;0 1]),T[2ratio,ratio*term];objective_constant=T(7),
            row_lower=[T(0),nothing],row_upper=[T(0),nothing],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original=deepcopy(problem)
        result=JSimplex.aggregate_singleton_equalities(problem)
        @test size(result.problem.A)==(2,1)
        @test only(result.problem.objective)==zero(T)
        @test numerator(only(result.problem.objective))==0 && denominator(only(result.problem.objective))==1
        @test result.problem.objective_constant==7
        @test JSimplex.postsolve_primal(result,T[0])==T[0,0]
        @test problem.objective==original.objective && problem.A.nzval==original.A.nzval
    end
end

@testset "Singleton aggregation skips exact retained-cost cancellation" begin
function singleton_cancelled_retained_cost_probe(kind; count=128, T=Float64)
    ratio=kind==:unit_positive ? 1 : kind==:unit_negative ? -1 : kind==:negative ? -3 : kind==:zero_ratio ? 0 : 3
    old=kind==:nonzero_cost ? T(5) : T(3ratio)
    prices=T[isodd(i) ? 2ratio : -2ratio for i in 1:count]
    A=hcat(sparse(1:count,1:count,fill(T(2),count),count,count),sparse(fill(T(3),count,1)))
    problem=LinearProblem(A,[prices;old];objective_constant=T(7),
        row_lower=fill(T(4),count),row_upper=fill(T(4),count),
        column_lower=[ones(T,count);nothing],column_upper=[fill(T(3),count);nothing])
    return problem,JSimplex.aggregate_singleton_equalities
end
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive,:negative,:unit_positive,:unit_negative,:nonzero_cost,:zero_ratio), count in (3,4)
        problem,pass=singleton_cancelled_retained_cost_probe(kind;count,T)
        original=deepcopy(problem);result=pass(problem)
        ratios=problem.objective[1:count]./2
        @test result.problem.A==fill(T(3),count,1)
        @test result.problem.row_lower==fill(Bound(T(-2)),count)
        @test result.problem.row_upper==fill(Bound(T(2)),count)
        expected=problem.objective[end]-3sum(ratios)
        @test result.problem.objective==T[expected]
        @test !iszero(expected) || isequal(only(result.problem.objective),zero(T))
        @test result.problem.objective_constant==T(7)+4sum(ratios)
        primal=T[0];restored=JSimplex.postsolve_primal(result,primal)
        @test restored==[fill(T(2),count);zero(T)]
        @test problem.objective_constant+sum(problem.objective.*restored)==result.problem.objective_constant+sum(result.problem.objective.*primal)
        m,n=size(result.problem.A)
        for state in (JSimplex.AT_LOWER,JSimplex.AT_UPPER)
            basis=JSimplex.Basis(collect(n+1:n+m),[fill(state,n);fill(JSimplex.BASIC,m)])
            restored_basis=JSimplex.restore_basis(result,basis)
            @test restored_basis.basic_indices==collect(1:count)
            @test restored_basis.states[count+1]==state
        end
        derived=only(result.problem.objective)+one(T)
        @test derived==expected+one(T)
        result.problem.objective[1]+=one(T);result.problem.A.nzval[1]+=one(T)
        result.problem.row_upper[1]=Bound(T(20))
        @test isequal(problem.objective_constant,original.objective_constant)
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective)
        @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
        @test isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
    for (kind,limit) in ((:positive,26100),(:negative,26100),(:unit_positive,24052),(:unit_negative,24052),(:nonzero_cost,27130),(:zero_ratio,19828))
        problem,pass=singleton_cancelled_retained_cost_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
