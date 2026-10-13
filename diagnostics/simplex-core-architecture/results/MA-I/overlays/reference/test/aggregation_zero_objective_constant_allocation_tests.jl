using SparseArrays

@testset "Zero objective constants preserve aggregation results" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), ratio in (-3,-1,1,3), rhs in (-4,-1,1,4), negative in (false,true), implied in (false,true)
        constant=negative ? -zero(T) : zero(T)
        problem=LinearProblem(sparse(T[2 3;6 5]),T[2ratio,5];objective_constant=constant,
            row_lower=T[rhs,-100],row_upper=T[rhs,100],
            column_lower=[implied ? nothing : T(1),nothing],column_upper=[implied ? nothing : T(3),nothing])
        original=deepcopy(problem)
        result=JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A)==(implied ? 1 : 2,1)
        @test result.problem.objective_constant==T(ratio*rhs)
        @test result.problem.objective==T[5-3ratio]
        @test result.problem.A[end,1]==T(-4)
        @test JSimplex.bound_value(result.problem.row_lower[end])==-100-3rhs && JSimplex.bound_value(result.problem.row_upper[end])==100-3rhs
        x=JSimplex.postsolve_primal(result,T[2])
        @test x==T[(rhs-6)/2,2]
        @test sum(problem.objective.*x)+problem.objective_constant==2only(result.problem.objective)+result.problem.objective_constant
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Zero-constant detection uses committed state across three candidates" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), ratio in (-3,-1,1,3), initial in (0,-ratio), rhs in ((1,1,1),(1,-1,2))
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

@testset "Direct constant products retain BigFloat representation gates" begin
    for side in (:ratio,:rhs), mode in (:exact,:tiny,:inexact), ambient in (32,64,256), direction in (-1,1)
        problem=setprecision(BigFloat,256) do
            epsilon=BigFloat(2)^(-200)
            value=direction*(mode==:tiny ? epsilon : mode==:exact ? BigFloat(3) : BigFloat(3)+epsilon)
            ratio,rhs=side==:ratio ? (value,BigFloat(1)) : (BigFloat(1),value)
            A=sparse([1,2,1],[1,1,2],BigFloat[2,0,1],2,2)
            LinearProblem(A,BigFloat[2ratio,ratio];objective_constant=BigFloat(-0.0),
                row_lower=[rhs,nothing],row_upper=[rhs,nothing],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        saved_cost=JSimplex._exact_rational.(problem.objective)
        saved_rhs=JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[1]))
        expected=saved_cost[1]/2*saved_rhs
        setprecision(BigFloat,ambient) do
            result=JSimplex.aggregate_sparse_equalities(problem)
            if mode==:inexact && ambient<256
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            else
                @test size(result.problem.A)==(1,1)
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

@testset "Direct constant products preserve non-dyadic rational values" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), direction in (-1,1), side in (:ratio,:rhs)
        value=T((BigInt(1)<<300)+1,BigInt(den))
        ratio,rhs=side==:ratio ? (value,T(direction)) : (T(direction),value)
        A=sparse([1,2,1],[1,1,2],T[2,0,1],2,2)
        problem=LinearProblem(A,T[2ratio,ratio];objective_constant=zero(T),
            row_lower=[rhs,nothing],row_upper=[rhs,nothing],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original=deepcopy(problem)
        result=JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A)==(1,1)
        @test result.problem.objective_constant==ratio*rhs
        @test gcd(numerator(result.problem.objective_constant),denominator(result.problem.objective_constant))==1
        @test result.problem.objective==T[0]
        @test JSimplex.postsolve_primal(result,T[0])==T[rhs/2,0]
        @test problem.objective_constant==original.objective_constant && problem.objective==original.objective && problem.row_lower==original.row_lower
    end
end

@testset "Zero-constant shortcut preserves rejection and tiny nonzero constants" begin
    for T in (Float32,Float64), direction in (-1,1), mode in (:overflow,:half_subnormal,:nonzero_constant)
        cost=mode==:overflow ? T(2direction) : mode==:half_subnormal ? T(direction)*nextfloat(zero(T)) : T(direction)
        pivot=mode==:half_subnormal ? T(2) : T(1)
        rhs=mode==:overflow ? floatmax(T) : T(1)
        constant=mode==:nonzero_constant ? nextfloat(zero(T)) : -zero(T)
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

@testset "Sparse aggregation avoids adding products to zero constants" begin
function aggregation_zero_objective_constant_probe(kind; count=128)
    ratio = kind == :unit_positive ? 1.0 : kind == :unit_negative ? -1.0 : kind == :negative ? -3.0 : 3.0
    rhs = kind == :zero_rhs ? 0.0 : 4.0
    constant = kind == :nonzero_constant ? 7.0 : kind in (:negative,:unit_negative) ? -0.0 : 0.0
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

    for (kind,limit) in ((:positive,33600),(:negative,33600),(:unit_positive,31300),(:unit_negative,31800),(:nonzero_constant,34400),(:zero_rhs,29500))
        problem,pass=aggregation_zero_objective_constant_probe(kind)
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
