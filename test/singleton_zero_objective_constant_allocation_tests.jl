using SparseArrays

@testset "Singleton: Zero objective constants preserve aggregation results" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), ratio in (-3,-1,1,3), rhs in (-4,-1,1,4), negative in (false,true), implied in (false,true)
        constant=negative ? -zero(T) : zero(T)
        problem=LinearProblem(sparse(T[2 3;0 1]),T[2ratio,5];objective_constant=constant,
            row_lower=T[rhs,-100],row_upper=T[rhs,100],
            column_lower=[implied ? nothing : T(1),nothing],column_upper=[implied ? nothing : T(3),nothing])
        original=deepcopy(problem)
        result=JSimplex.aggregate_singleton_equalities(problem)
        @test size(result.problem.A)==(2,1)
        @test result.problem.objective_constant==T(ratio*rhs)
        @test result.problem.objective==T[5-3ratio]
        @test result.problem.A[end,1]==T(1)
        @test JSimplex.bound_value(result.problem.row_lower[end])==-100 && JSimplex.bound_value(result.problem.row_upper[end])==100
        x=JSimplex.postsolve_primal(result,T[2])
        @test x==T[(rhs-6)/2,2]
        @test sum(problem.objective.*x)+problem.objective_constant==2only(result.problem.objective)+result.problem.objective_constant
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Singleton: Zero-constant detection uses committed state across three candidates" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), ratio in (-3,-1,1,3), initial in (0,-ratio), rhs in ((1,1,1),(1,-1,2))
        problem=LinearProblem(sparse(T[2 0 0 3;0 2 0 3;0 0 2 3;0 0 0 5]),T[2ratio,2ratio,2ratio,5];objective_constant=T(initial),
            row_lower=[T(rhs[1]),T(rhs[2]),T(rhs[3]),nothing],row_upper=T[rhs[1],rhs[2],rhs[3],20],column_lower=fill(nothing,4),column_upper=fill(nothing,4))
        original=deepcopy(problem)
        result=JSimplex.aggregate_singleton_equalities(problem)
        @test size(result.problem.A)==(4,1)
        @test result.problem.objective_constant==T(initial+ratio*sum(rhs))
        @test result.problem.objective==T[5-9ratio]
        @test JSimplex.bound_value(result.problem.row_upper[end])==T(20)
        @test JSimplex.postsolve_primal(result,T[2])==T[(rhs[1]-6)/2,(rhs[2]-6)/2,(rhs[3]-6)/2,2]
        @test isequal(problem.objective_constant,original.objective_constant) && isequal(problem.objective,original.objective) && isequal(problem.A.nzval,original.A.nzval)
    end
end

@testset "Singleton: Direct constant products retain BigFloat representation gates" begin
    for side in (:ratio,:rhs), mode in (:exact,:tiny,:inexact), ambient in (32,64,256), direction in (-1,1)
        problem=setprecision(BigFloat,256) do
            epsilon=BigFloat(2)^(-200)
            value=direction*(mode==:tiny ? epsilon : mode==:exact ? BigFloat(3) : BigFloat(3)+epsilon)
            ratio,rhs=side==:ratio ? (value,BigFloat(1)) : (BigFloat(1),value)
            A=sparse(BigFloat[2 1;0 1])
            LinearProblem(A,BigFloat[2ratio,ratio];objective_constant=BigFloat(-0.0),
                row_lower=[rhs,nothing],row_upper=[rhs,nothing],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        saved_cost=JSimplex._exact_rational.(problem.objective)
        saved_rhs=JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[1]))
        expected=saved_cost[1]/2*saved_rhs
        setprecision(BigFloat,ambient) do
            result=JSimplex.aggregate_singleton_equalities(problem)
            if mode==:inexact && ambient<256
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            else
                @test size(result.problem.A)==(2,1)
                @test JSimplex._exact_rational(result.problem.objective_constant)==expected
                @test precision(result.problem.objective_constant)==ambient
                @test result.problem.objective==BigFloat[0]
            end
            @test JSimplex._exact_rational.(problem.objective)==saved_cost
            @test JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[1]))==saved_rhs
            @test iszero(problem.objective_constant) && signbit(problem.objective_constant)
        end
    end
end

@testset "Singleton: Direct constant products preserve non-dyadic rational values" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), direction in (-1,1), side in (:ratio,:rhs)
        value=T((BigInt(1)<<300)+1,BigInt(den))
        ratio,rhs=side==:ratio ? (value,T(direction)) : (T(direction),value)
        A=sparse(T[2 1;0 1])
        problem=LinearProblem(A,T[2ratio,ratio];objective_constant=zero(T),
            row_lower=[rhs,nothing],row_upper=[rhs,nothing],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original=deepcopy(problem)
        result=JSimplex.aggregate_singleton_equalities(problem)
        @test size(result.problem.A)==(2,1)
        @test result.problem.objective_constant==ratio*rhs
        @test gcd(numerator(result.problem.objective_constant),denominator(result.problem.objective_constant))==1
        @test result.problem.objective==T[0]
        @test JSimplex.postsolve_primal(result,T[0])==T[rhs/2,0]
        @test problem.objective_constant==original.objective_constant && problem.objective==original.objective && problem.row_lower==original.row_lower
    end
end

@testset "Singleton: Zero-constant shortcut preserves rejection and tiny nonzero constants" begin
    for T in (Float32,Float64), direction in (-1,1), mode in (:overflow,:half_subnormal,:nonzero_constant)
        cost=mode==:overflow ? T(2direction) : mode==:half_subnormal ? T(direction)*nextfloat(zero(T)) : T(direction)
        pivot=mode==:half_subnormal ? T(2) : T(1)
        rhs=mode==:overflow ? floatmax(T) : T(1)
        constant=mode==:nonzero_constant ? nextfloat(zero(T)) : -zero(T)
        A=sparse(T[pivot 1;0 1])
        problem=LinearProblem(A,T[cost,0];objective_constant=constant,row_lower=[rhs,nothing],row_upper=[rhs,nothing],
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original=deepcopy(problem)
        result=JSimplex.aggregate_singleton_equalities(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test isequal(problem.objective_constant,original.objective_constant) && isequal(problem.objective,original.objective) && isequal(problem.A.nzval,original.A.nzval)
    end
end

@testset "Singleton aggregation skips addition to the current zero constant" begin
function singleton_zero_objective_constant_probe(kind; count=128, T=Float64)
    ratio=kind==:unit_positive ? 1 : kind==:unit_negative ? -1 : kind==:negative ? -3 : 3
    rhs=kind==:zero_rhs ? zero(T) : T(4)
    initial=kind==:nonzero_constant ? T(7) : ratio<0 ? -zero(T) : zero(T)
    prices=T[isodd(i) ? 2ratio : -2ratio for i in 1:count]
    A=hcat(sparse(1:count,1:count,fill(T(2),count),count,count),sparse(ones(T,count,1)))
    problem=LinearProblem(A,[prices;T(2)];objective_constant=initial,
        row_lower=fill(rhs,count),row_upper=fill(rhs,count),
        column_lower=[ones(T,count);nothing],column_upper=[fill(T(3),count);nothing])
    return problem,JSimplex.aggregate_singleton_equalities
end

    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive,:negative,:unit_positive,:unit_negative,:nonzero_constant,:zero_rhs), count in (3,4)
        problem,pass=singleton_zero_objective_constant_probe(kind;count,T)
        original=deepcopy(problem);result=pass(problem)
        ratios=problem.objective[1:count]./2;rhs=bound_value(problem.row_upper[1])
        @test result.problem.A==ones(T,count,1)
        @test result.problem.row_lower==fill(Bound(rhs-6),count)
        @test result.problem.row_upper==fill(Bound(rhs-2),count)
        @test result.problem.objective==T[2-sum(ratios)]
        expected=problem.objective_constant+rhs*sum(ratios)
        @test result.problem.objective_constant==expected
        @test !iszero(expected) || isequal(result.problem.objective_constant,zero(T))
        primal=T[rhs-4];restored=JSimplex.postsolve_primal(result,primal)
        @test restored==[fill(T(2),count);only(primal)]
        @test problem.objective_constant+sum(problem.objective.*restored)==result.problem.objective_constant+sum(result.problem.objective.*primal)
        m,n=size(result.problem.A)
        for state in (JSimplex.AT_LOWER,JSimplex.AT_UPPER)
            basis=JSimplex.Basis(collect(n+1:n+m),[fill(state,n);fill(JSimplex.BASIC,m)])
            restored_basis=JSimplex.restore_basis(result,basis)
            @test restored_basis.basic_indices==collect(1:count)
            @test restored_basis.states[count+1]==state
        end
        result.problem.objective[1]+=one(T)
        result.problem.A.nzval[1]+=one(T)
        result.problem.row_upper[1]=Bound(T(20))
        @test isequal(problem.objective_constant,original.objective_constant)
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective)
        @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
        @test isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
    for (kind,limit) in ((:positive,26638),(:negative,26638),(:unit_positive,25614),(:unit_negative,25614),(:nonzero_constant,27386),(:zero_rhs,23028))
        problem,pass=singleton_zero_objective_constant_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
