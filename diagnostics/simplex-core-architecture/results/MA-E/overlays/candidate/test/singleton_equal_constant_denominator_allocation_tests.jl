using SparseArrays

@testset "Singleton: Equal constant denominators preserve aggregation results" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), ratio in (-3,-1,1,3), rhs in (-1,-1//2,1//2,1), mode in (:cancel,:sum,:same,:unequal,:zero)
        product=T(ratio*rhs)
        constant=mode==:cancel ? -product : mode==:sum ? T(rhs) : mode==:same ? product : mode==:unequal ? product/T(2) : zero(T)
        implied=mode!=:same
        problem=LinearProblem(sparse(T[2 3;0 1]),T[2ratio,5];objective_constant=constant,
            row_lower=T[rhs,-100],row_upper=T[rhs,100],
            column_lower=[implied ? nothing : T(1),nothing],column_upper=[implied ? nothing : T(3),nothing])
        original=deepcopy(problem)
        result=JSimplex.aggregate_singleton_equalities(problem)
        @test size(result.problem.A)==(2,1)
        @test result.problem.objective_constant==constant+product
        @test result.problem.objective==T[5-3ratio]
        @test result.problem.A[end,1]==T(1)
        @test JSimplex.bound_value(result.problem.row_lower[end])==-100 && JSimplex.bound_value(result.problem.row_upper[end])==100
        x=JSimplex.postsolve_primal(result,T[2])
        @test x==T[(rhs-6)/2,2]
        @test sum(problem.objective.*x)+problem.objective_constant==2only(result.problem.objective)+result.problem.objective_constant
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Singleton: Equal-denominator sums use committed constants across candidates" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), ratio in (-3//2,-1//2,1//2,3//2), initial in (0,1//2,-ratio), rhs in ((1,1,1),(1,-1,2))
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

@testset "Singleton: Equal-denominator constant sums retain stored precision and residuals" begin
    for side in (:ratio,:rhs), mode in (:exact,:cancel,:tail,:inexact), ambient in (32,64,256), direction in (-1,1)
        problem=setprecision(BigFloat,256) do
            epsilon=BigFloat(2)^(-200)
            value=direction*(BigFloat(3)+(mode==:exact ? zero(BigFloat) : epsilon))
            ratio,rhs=side==:ratio ? (value,BigFloat(1)) : (BigFloat(1),value)
            constant=mode==:exact ? BigFloat(5direction) : mode==:cancel ? -value : mode==:tail ? direction*(-BigFloat(3)+epsilon) : direction*(BigFloat(5)+epsilon)
            A=sparse(BigFloat[2 1;0 1])
            LinearProblem(A,BigFloat[2ratio,ratio];objective_constant=constant,
                row_lower=[rhs,nothing],row_upper=[rhs,nothing],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        saved_cost=JSimplex._exact_rational.(problem.objective)
        saved_rhs=JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[1]))
        saved_constant=JSimplex._exact_rational(problem.objective_constant)
        expected=saved_constant+saved_cost[1]/2*saved_rhs
        setprecision(BigFloat,ambient) do
            result=JSimplex.aggregate_singleton_equalities(problem)
            if mode==:inexact && ambient<256
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            else
                @test size(result.problem.A)==(2,1)
                @test JSimplex._exact_rational(result.problem.objective_constant)==expected
                @test precision(result.problem.objective_constant)==ambient
                @test mode==:cancel ? !signbit(result.problem.objective_constant) : !iszero(result.problem.objective_constant)
            end
            @test JSimplex._exact_rational.(problem.objective)==saved_cost
            @test JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[1]))==saved_rhs
            @test JSimplex._exact_rational(problem.objective_constant)==saved_constant
        end
    end
end

@testset "Singleton: Constant sums canonicalize large non-dyadic fractions" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), factor in (-2,-1,1,2,4), direction in (-1,1)
        ratio=T((BigInt(1)<<300)+1,BigInt(den));rhs=T(direction);constant=factor*ratio
        A=sparse(T[2 1;0 1])
        problem=LinearProblem(A,T[2ratio,ratio];objective_constant=constant,
            row_lower=[rhs,nothing],row_upper=[rhs,nothing],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original=deepcopy(problem)
        result=JSimplex.aggregate_singleton_equalities(problem)
        expected=constant+ratio*rhs
        @test size(result.problem.A)==(2,1)
        @test result.problem.objective_constant==expected && denominator(result.problem.objective_constant)==denominator(expected)
        @test gcd(numerator(result.problem.objective_constant),denominator(result.problem.objective_constant))==1
        @test result.problem.objective==T[0]
        @test JSimplex.postsolve_primal(result,T[0])==T[rhs/2,0]
        @test problem.objective_constant==original.objective_constant && problem.objective==original.objective && problem.row_lower==original.row_lower
    end
end

@testset "Singleton: Constant denominator shortcut preserves representability rejection" begin
    for T in (Float32,Float64), direction in (-1,1), mode in (:overflow,:half_subnormal)
        cost=mode==:overflow ? T(direction) : T(direction)*nextfloat(zero(T))
        pivot=mode==:overflow ? T(1) : T(2)
        rhs=mode==:overflow ? floatmax(T) : T(1)
        constant=mode==:overflow ? T(direction)*floatmax(T) : -T(direction)*nextfloat(zero(T))
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

@testset "Singleton aggregation avoids general shared-denominator constant addition" begin
function singleton_equal_constant_denominator_probe(kind; count=256, T=Float64)
    rhs=kind in (:cancel_integer,:sum_integer) ? one(T) : kind==:zero_rhs ? zero(T) : T(1)/2
    initial=kind==:cancel_integer ? T(3) : kind==:cancel_fraction ? T(3)/2 :
        kind in (:sum_integer,:zero_rhs) ? T(5) : kind==:sum_fraction ? T(1)/2 : T(1)/8
    prices=T[isodd(i) ? -6 : 6 for i in 1:count]
    A=hcat(sparse(1:count,1:count,fill(T(2),count),count,count),sparse(ones(T,count,1)))
    problem=LinearProblem(A,[prices;T(2)];objective_constant=initial,
        row_lower=fill(rhs,count),row_upper=fill(rhs,count),
        column_lower=[ones(T,count);nothing],column_upper=[fill(T(3),count);nothing])
    return problem,JSimplex.aggregate_singleton_equalities
end
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:cancel_integer,:cancel_fraction,:sum_integer,:sum_fraction,:unequal_denominator,:zero_rhs), count in (3,4)
        problem,pass=singleton_equal_constant_denominator_probe(kind;count,T)
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
    for (kind,limit) in ((:cancel_integer,50123),(:cancel_fraction,53387),(:sum_integer,51595),(:sum_fraction,54987),(:unequal_denominator,55173),(:zero_rhs,46469))
        problem,pass=singleton_equal_constant_denominator_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
