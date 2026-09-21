using SparseArrays

@testset "Equal constant denominators preserve aggregation results" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), ratio in (-3,-1,1,3), rhs in (-1,-1//2,1//2,1), mode in (:cancel,:sum,:same,:unequal,:zero)
        product=T(ratio*rhs)
        constant=mode==:cancel ? -product : mode==:sum ? T(rhs) : mode==:same ? product : mode==:unequal ? product/T(2) : zero(T)
        implied=mode!=:same
        problem=LinearProblem(sparse(T[2 3;6 5]),T[2ratio,5];objective_constant=constant,
            row_lower=T[rhs,-100],row_upper=T[rhs,100],
            column_lower=[implied ? nothing : T(1),nothing],column_upper=[implied ? nothing : T(3),nothing])
        original=deepcopy(problem)
        result=JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A)==(implied ? 1 : 2,1)
        @test result.problem.objective_constant==constant+product
        @test result.problem.objective==T[5-3ratio]
        @test result.problem.A[end,1]==T(-4)
        @test JSimplex.bound_value(result.problem.row_lower[end])==-100-3rhs && JSimplex.bound_value(result.problem.row_upper[end])==100-3rhs
        x=JSimplex.postsolve_primal(result,T[2])
        @test x==T[(rhs-6)/2,2]
        @test sum(problem.objective.*x)+problem.objective_constant==2only(result.problem.objective)+result.problem.objective_constant
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Equal-denominator sums use committed constants across candidates" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), ratio in (-3//2,-1//2,1//2,3//2), initial in (0,1//2,-ratio), rhs in ((1,1,1),(1,-1,2))
        problem=LinearProblem(sparse(T[2 0 0 3;0 2 0 3;0 0 2 3;2 2 2 5]),T[2ratio,2ratio,2ratio,5];objective_constant=T(initial),
            row_lower=[T(rhs[1]),T(rhs[2]),T(rhs[3]),nothing],row_upper=T[rhs[1],rhs[2],rhs[3],20],column_lower=fill(nothing,4),column_upper=fill(nothing,4))
        original=deepcopy(problem)
        result=JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A)==(1,1)
        @test result.problem.objective_constant==T(initial+ratio*sum(rhs))
        @test result.problem.objective==T[5-9ratio]
        @test JSimplex.bound_value(result.problem.row_upper[1])==T(20-sum(rhs))
        @test JSimplex.postsolve_primal(result,T[2])==T[(rhs[1]-6)/2,(rhs[2]-6)/2,(rhs[3]-6)/2,2]
        @test isequal(problem.objective_constant,original.objective_constant) && isequal(problem.objective,original.objective) && isequal(problem.A.nzval,original.A.nzval)
    end
end

@testset "Equal-denominator constant sums retain stored precision and residuals" begin
    for side in (:ratio,:rhs), mode in (:exact,:cancel,:tail,:inexact), ambient in (32,64,256), direction in (-1,1)
        problem=setprecision(BigFloat,256) do
            epsilon=BigFloat(2)^(-200)
            value=direction*(BigFloat(3)+(mode==:exact ? zero(BigFloat) : epsilon))
            ratio,rhs=side==:ratio ? (value,BigFloat(1)) : (BigFloat(1),value)
            constant=mode==:exact ? BigFloat(5direction) : mode==:cancel ? -value : mode==:tail ? direction*(-BigFloat(3)+epsilon) : direction*(BigFloat(5)+epsilon)
            A=sparse([1,2,1],[1,1,2],BigFloat[2,0,1],2,2)
            LinearProblem(A,BigFloat[2ratio,ratio];objective_constant=constant,
                row_lower=[rhs,nothing],row_upper=[rhs,nothing],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        saved_cost=JSimplex._exact_rational.(problem.objective)
        saved_rhs=JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[1]))
        saved_constant=JSimplex._exact_rational(problem.objective_constant)
        expected=saved_constant+saved_cost[1]/2*saved_rhs
        setprecision(BigFloat,ambient) do
            result=JSimplex.aggregate_sparse_equalities(problem)
            if mode==:inexact && ambient<256
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            else
                @test size(result.problem.A)==(1,1)
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

@testset "Constant sums canonicalize large non-dyadic fractions" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), factor in (-2,-1,1,2,4), direction in (-1,1)
        ratio=T((BigInt(1)<<300)+1,BigInt(den));rhs=T(direction);constant=factor*ratio
        A=sparse([1,2,1],[1,1,2],T[2,0,1],2,2)
        problem=LinearProblem(A,T[2ratio,ratio];objective_constant=constant,
            row_lower=[rhs,nothing],row_upper=[rhs,nothing],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original=deepcopy(problem)
        result=JSimplex.aggregate_sparse_equalities(problem)
        expected=constant+ratio*rhs
        @test size(result.problem.A)==(1,1)
        @test result.problem.objective_constant==expected && denominator(result.problem.objective_constant)==denominator(expected)
        @test gcd(numerator(result.problem.objective_constant),denominator(result.problem.objective_constant))==1
        @test result.problem.objective==T[0]
        @test JSimplex.postsolve_primal(result,T[0])==T[rhs/2,0]
        @test problem.objective_constant==original.objective_constant && problem.objective==original.objective && problem.row_lower==original.row_lower
    end
end

@testset "Constant denominator shortcut preserves representability rejection" begin
    for T in (Float32,Float64), direction in (-1,1), mode in (:overflow,:half_subnormal)
        cost=mode==:overflow ? T(direction) : T(direction)*nextfloat(zero(T))
        pivot=mode==:overflow ? T(1) : T(2)
        rhs=mode==:overflow ? floatmax(T) : T(1)
        constant=mode==:overflow ? T(direction)*floatmax(T) : -T(direction)*nextfloat(zero(T))
        A=sparse([1,2,1],[1,1,2],T[pivot,0,1],2,2)
        problem=LinearProblem(A,T[cost,0];objective_constant=constant,row_lower=[rhs,nothing],row_upper=[rhs,nothing],
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original=deepcopy(problem)
        result=JSimplex.aggregate_sparse_equalities(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test isequal(problem.objective_constant,original.objective_constant) && isequal(problem.objective,original.objective) && isequal(problem.A.nzval,original.A.nzval)
    end
end

@testset "Sparse aggregation avoids general equal-denominator constant addition" begin
function aggregation_equal_constant_denominator_probe(kind; count=128)
    ratio = -3.0
    rhs = kind in (:cancel_integer,:sum_integer) ? 1.0 : 0.5
    constant = kind == :cancel_integer ? 3.0 : kind == :cancel_fraction ? 1.5 :
        kind == :sum_integer ? 5.0 : kind == :sum_fraction ? 0.5 : kind == :zero_constant ? 0.0 : 1.0
    odd = collect(1:2:2count); even = odd .+ 1
    # The retained column has degree one, so a rejected x pivot cannot be
    # replaced by a y pivot. Every block fails the retained-cost exactness gate.
    A = sparse(vcat(odd,odd,even),vcat(odd,even,odd),
        vcat(fill(2.0,count),fill(3.0,count),fill(6.0,count)),2count,2count)
    problem = LinearProblem(A,[isodd(i) ? 2ratio : nextfloat(0.0) for i in 1:2count];objective_constant=constant,
        row_lower=Union{Nothing,Float64}[isodd(i) ? rhs : nothing for i in 1:2count],
        row_upper=[isodd(i) ? rhs : 20.0 for i in 1:2count],
        column_lower=Union{Nothing,Float64}[isodd(i) ? 1.0 : nothing for i in 1:2count],
        column_upper=Union{Nothing,Float64}[isodd(i) ? 3.0 : nothing for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

    for (kind,limit) in ((:cancel_integer,32500),(:cancel_fraction,33580),(:sum_integer,32950),(:sum_fraction,34030),(:unequal_denominator,34400),(:zero_constant,33200))
        problem,pass=aggregation_equal_constant_denominator_probe(kind)
        original=deepcopy(problem)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
        result=pass(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant)
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end
