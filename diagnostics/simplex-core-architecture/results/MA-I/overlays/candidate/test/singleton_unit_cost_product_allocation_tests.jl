using SparseArrays

@testset "Singleton: Unit cost products preserve aggregation objectives and projections" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), ratio in (-3,-1,0,1,3), term in (-3,-1,1,3), implied in (false,true)
        problem = LinearProblem(sparse(T[2 term;0 1]),T[2ratio,5];objective_constant=T(7),
            row_lower=T[4,-100],row_upper=T[4,100],
            column_lower=[implied ? nothing : T(1),nothing],column_upper=[implied ? nothing : T(3),nothing])
        original = deepcopy(problem)
        result = JSimplex.aggregate_singleton_equalities(problem)
        @test size(result.problem.A) == (2,1)
        @test result.problem.objective == T[5-ratio*term]
        @test result.problem.objective_constant == T(7+4ratio)
        @test result.problem.A[end,1] == T(1)
        @test JSimplex.bound_value(result.problem.row_lower[end]) == -100 && JSimplex.bound_value(result.problem.row_upper[end]) == 100
        x = JSimplex.postsolve_primal(result,T[2])
        @test x == T[2-term,2]
        @test sum(problem.objective.*x)+problem.objective_constant == 2only(result.problem.objective)+result.problem.objective_constant
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Singleton: Unit cost products use committed costs across candidates" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), ratios in ((1,-1),(-1,3),(3,-3),(0,1)), terms in ((3,-1),(1,-1))
        r1,r2=ratios; t1,t2=terms
        problem = LinearProblem(sparse(T[2 0 t1;0 2 t2;0 0 5]),T[2r1,2r2,5];objective_constant=T(7),
            row_lower=[T(4),T(4),nothing],row_upper=T[4,4,20],
            column_lower=fill(nothing,3),column_upper=fill(nothing,3))
        original = deepcopy(problem)
        result = JSimplex.aggregate_singleton_equalities(problem)
        @test size(result.problem.A) == (3,1)
        @test result.problem.objective == T[5-r1*t1-r2*t2]
        @test result.problem.objective_constant == T(7+4r1+4r2)
        @test result.problem.A[:,1] == T[t1,t2,5]
        @test JSimplex.postsolve_primal(result,T[2]) == T[2-t1,2-t2,2]
        @test isequal(problem.objective,original.objective) && isequal(problem.A.nzval,original.A.nzval)
    end
end

@testset "Singleton cost products distinguish both stored unit neighbors" begin
    for side in (:ratio,:term), mode in (:exact,:near,:tail,:cancel), ambient in (32,64,256), direction in (-1,1)
        problem=setprecision(BigFloat,256) do
            epsilon=BigFloat(2)^(-200)
            unit=direction*(BigFloat(1)+(mode==:exact ? zero(BigFloat) : epsilon))
            ratio,term=side==:ratio ? (unit,BigFloat(3)) : (BigFloat(3),unit)
            old=mode==:tail ? BigFloat(3direction) : mode==:cancel ? ratio*term : BigFloat(5)
            LinearProblem(sparse(BigFloat[2 term;0 1]),BigFloat[2ratio,old];objective_constant=BigFloat(7),
                row_lower=[BigFloat(0),nothing],row_upper=[BigFloat(0),nothing],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        saved_cost=JSimplex._exact_rational.(problem.objective)
        saved_matrix=JSimplex._exact_rational.(problem.A.nzval)
        expected=saved_cost[2]-saved_cost[1]/2*JSimplex._exact_rational(problem.A[1,2])
        setprecision(BigFloat,ambient) do
            result=JSimplex.aggregate_singleton_equalities(problem)
            if mode==:near && ambient<256
                @test result.problem===problem && isempty(result.postsolve_stack)
            else
                @test size(result.problem.A)==(2,1)
                @test JSimplex._exact_rational(only(result.problem.objective))==expected
                @test precision(only(result.problem.objective))==ambient
                @test result.problem.objective_constant==7
                @test !iszero(expected) || isequal(only(result.problem.objective),zero(BigFloat))
            end
            @test JSimplex._exact_rational.(problem.objective)==saved_cost
            @test JSimplex._exact_rational.(problem.A.nzval)==saved_matrix
            @test all(precision(x)==256 for x in problem.objective)
        end
    end
end

@testset "Singleton: Unit cost products retain large non-dyadic rational arithmetic" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), direction in (-1,1), side in (:ratio,:term)
        value=T((BigInt(1)<<300)+1,BigInt(den))
        ratio,term=side == :ratio ? (T(direction),value) : (value,T(direction))
        problem=LinearProblem(sparse(T[2 term;0 1]),T[2ratio,5];objective_constant=T(7),
            row_lower=[T(0),nothing],row_upper=[T(0),nothing],
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original=deepcopy(problem)
        result=JSimplex.aggregate_singleton_equalities(problem)
        expected=5-ratio*term
        @test size(result.problem.A)==(2,1)
        @test only(result.problem.objective)==expected
        @test gcd(numerator(only(result.problem.objective)),denominator(only(result.problem.objective)))==1
        @test result.problem.objective_constant==7
        @test JSimplex.postsolve_primal(result,T[0])==T[0,0]
        @test problem.objective==original.objective && problem.A.nzval==original.A.nzval
    end
end

@testset "Singleton: Unit cost products retain representability rejection" begin
    for T in (Float32,Float64), direction in (-1,1), mode in (:overflow,:half_subnormal)
        cost=mode == :overflow ? T(direction) : T(direction)*nextfloat(zero(T))
        term=mode == :overflow ? floatmax(T) : T(1)
        old=mode == :overflow ? -T(direction)*floatmax(T) : zero(T)
        A=sparse(T[(mode == :overflow ? 1 : 2) term;0 1])
        problem=LinearProblem(A,T[cost,old];row_lower=[T(0),nothing],row_upper=[T(0),nothing],
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original=deepcopy(problem)
        result=JSimplex.aggregate_singleton_equalities(problem)
        @test result.problem===problem
        @test isempty(result.postsolve_stack)
        @test all(isfinite,result.problem.objective)
        @test isequal(problem.objective,original.objective) && isequal(problem.A.nzval,original.A.nzval)
    end
end

@testset "Singleton unit terms preserve permitted objective rounding" begin
    for T in (Float32,Float64), term in (-1,1), direction in (-1,1)
        problem=LinearProblem(sparse(T[3direction term;0 1]),T[1,0];objective_constant=T(7),
            row_lower=[zero(T),nothing],row_upper=[zero(T),nothing],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        result=JSimplex.aggregate_singleton_equalities(problem)
        @test size(result.problem.A)==(2,1)
        @test result.problem.objective==T[-T(term)/T(3direction)]
        @test result.problem.objective_constant==7
        @test JSimplex.postsolve_primal(result,T[0])==T[0,0]
    end
end

@testset "Singleton aggregation avoids signed-unit cost multiplication" begin
function singleton_unit_cost_product_probe(kind; count=128, T=Float64)
    ratio=kind==:ratio_positive ? one(T) : kind==:ratio_negative ? -one(T) : kind==:zero_ratio ? zero(T) : T(3)
    term=kind==:term_positive ? one(T) : kind==:term_negative ? -one(T) : T(3)
    A=hcat(sparse(1:count,1:count,fill(T(2),count),count,count),sparse(fill(term,count,1)))
    problem=LinearProblem(A,[fill(2ratio,count);T(2)];objective_constant=T(7),
        row_lower=fill(T(4),count),row_upper=fill(T(4),count),
        column_lower=[ones(T,count);nothing],column_upper=[fill(T(3),count);nothing])
    return problem,JSimplex.aggregate_singleton_equalities
end

    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:ratio_positive,:ratio_negative,:term_positive,:term_negative,:nonunit,:zero_ratio)
        count=4;problem,pass=singleton_unit_cost_product_probe(kind;count,T)
        original=deepcopy(problem);result=pass(problem)
        ratio=problem.objective[1]/2;term=problem.A[1,count+1]
        @test result.problem.A==fill(term,count,1)
        @test result.problem.row_lower==fill(Bound(T(-2)),count)
        @test result.problem.row_upper==fill(Bound(T(2)),count)
        @test result.problem.objective==T[2-count*ratio*term]
        @test result.problem.objective_constant==T(7)+4count*ratio
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
        result.problem.objective[1]+=one(T);result.problem.A.nzval[1]+=one(T)
        result.problem.row_upper[1]=Bound(T(20))
        @test isequal(problem.objective_constant,original.objective_constant)
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective)
        @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
        @test isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
    for (kind,limit) in ((:ratio_positive,25278),(:ratio_negative,25534),(:term_positive,26430),(:term_negative,26430),(:nonunit,27130),(:zero_ratio,20218))
        problem,pass=singleton_unit_cost_product_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
