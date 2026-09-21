using SparseArrays

@testset "Zero retained costs preserve aggregation objectives and projections" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), ratio in (-3,-1,0,1,3), term in (-3,-1,1,3), negative in (false,true), implied in (false,true)
        old=negative ? -zero(T) : zero(T)
        problem=LinearProblem(sparse(T[2 term;6 5]),T[2ratio,old];objective_constant=T(7),
            row_lower=T[4,-100],row_upper=T[4,100],
            column_lower=[implied ? nothing : T(1),nothing],column_upper=[implied ? nothing : T(3),nothing])
        original=deepcopy(problem)
        result=JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A)==(implied ? 1 : 2,1)
        @test isequal(only(result.problem.objective),iszero(ratio) ? zero(T) : T(-ratio*term))
        @test result.problem.objective_constant==T(7+4ratio)
        @test result.problem.A[end,1]==T(5-3term)
        @test JSimplex.bound_value(result.problem.row_lower[end])==-112 && JSimplex.bound_value(result.problem.row_upper[end])==88
        x=JSimplex.postsolve_primal(result,T[2])
        @test x==T[2-term,2]
        @test sum(problem.objective.*x)+problem.objective_constant==2only(result.problem.objective)+result.problem.objective_constant
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Zero retained cost detection uses committed objective updates" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), ratios in ((1,1),(1,-1),(-1,3),(0,1)), old in (0,3,6)
        r1,r2=ratios
        problem=LinearProblem(sparse(T[2 0 3;0 2 3;2 2 5]),T[2r1,2r2,old];objective_constant=T(7),
            row_lower=[T(4),T(4),nothing],row_upper=T[4,4,20],column_lower=fill(nothing,3),column_upper=fill(nothing,3))
        original=deepcopy(problem)
        result=JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A)==(1,1)
        @test result.problem.objective==T[old-3r1-3r2]
        @test result.problem.objective_constant==T(7+4r1+4r2)
        @test JSimplex.bound_value(result.problem.row_upper[1])==T(12)
        @test JSimplex.postsolve_primal(result,T[2])==T[-1,-1,2]
        @test isequal(problem.objective,original.objective) && isequal(problem.A.nzval,original.A.nzval)
    end
end

@testset "Negated cost products retain stored BigFloat precision gates" begin
    for side in (:ratio,:term), mode in (:exact,:tiny,:inexact), ambient in (32,64,256), direction in (-1,1)
        problem=setprecision(BigFloat,256) do
            epsilon=BigFloat(2)^(-200)
            value=direction*(mode==:tiny ? epsilon : mode==:exact ? BigFloat(3) : BigFloat(3)+epsilon)
            ratio,term=side==:ratio ? (value,BigFloat(1)) : (BigFloat(1),value)
            # Explicit zero keeps pivot degree two. Retained degree one prevents
            # an unrelated alternative pivot when the cost is not representable.
            A=sparse([1,2,1],[1,1,2],BigFloat[2,0,term],2,2)
            LinearProblem(A,BigFloat[2ratio,-0.0];objective_constant=BigFloat(7),
                row_lower=[BigFloat(0),nothing],row_upper=[BigFloat(0),nothing],
                column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        saved_cost=JSimplex._exact_rational.(problem.objective)
        saved_matrix=JSimplex._exact_rational.(problem.A.nzval)
        expected=-saved_cost[1]/2*JSimplex._exact_rational(problem.A[1,2])
        setprecision(BigFloat,ambient) do
            result=JSimplex.aggregate_sparse_equalities(problem)
            if mode==:inexact && ambient<256
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            else
                @test size(result.problem.A)==(1,1)
                @test JSimplex._exact_rational(only(result.problem.objective))==expected
                @test precision(only(result.problem.objective))==ambient
                @test result.problem.objective_constant==7
            end
            @test JSimplex._exact_rational.(problem.objective)==saved_cost
            @test JSimplex._exact_rational.(problem.A.nzval)==saved_matrix
        end
    end
end

@testset "Zero retained costs preserve non-dyadic rational products" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), direction in (-1,1), side in (:ratio,:term)
        value=T((BigInt(1)<<300)+1,BigInt(den))
        ratio,term=side==:ratio ? (value,T(direction)) : (T(direction),value)
        problem=LinearProblem(sparse(T[2 term;2 5]),T[2ratio,0];objective_constant=T(7),
            row_lower=[T(0),nothing],row_upper=[T(0),nothing],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original=deepcopy(problem)
        result=JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A)==(1,1)
        @test only(result.problem.objective)==-ratio*term
        @test gcd(numerator(only(result.problem.objective)),denominator(only(result.problem.objective)))==1
        @test result.problem.objective_constant==7
        @test JSimplex.postsolve_primal(result,T[0])==T[0,0]
        @test problem.objective==original.objective && problem.A.nzval==original.A.nzval
    end
end

@testset "Negated costs retain overflow subnormal and nonzero-cost rejection" begin
    for T in (Float32,Float64), direction in (-1,1), mode in (:overflow,:half_subnormal,:nonzero_cost)
        pivot=mode==:half_subnormal ? T(2) : T(1)
        cost=mode==:overflow ? T(2direction) : mode==:half_subnormal ? T(direction)*nextfloat(zero(T)) : T(1)
        term=mode==:overflow ? floatmax(T) : T(1)
        old=mode==:nonzero_cost ? T(direction)*nextfloat(zero(T)) : -zero(T)
        A=sparse([1,2,1],[1,1,2],T[pivot,0,term],2,2)
        problem=LinearProblem(A,T[cost,old];objective_constant=T(7),row_lower=[T(0),nothing],row_upper=[T(0),nothing],
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original=deepcopy(problem)
        result=JSimplex.aggregate_sparse_equalities(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test isequal(problem.objective,original.objective) && isequal(problem.A.nzval,original.A.nzval)
    end
end

@testset "Sparse aggregation avoids subtraction from zero retained costs" begin
function aggregation_zero_retained_cost_probe(kind; count=128)
    ratio = kind == :unit_positive ? 1.0 : kind == :unit_negative ? -1.0 : kind == :zero_ratio ? 0.0 : kind == :negative ? -3.0 : 3.0
    rhs = 4.0
    old_cost = kind == :nonzero_cost ? 5.0 : kind in (:negative,:unit_negative) ? -0.0 : 0.0
    term = 3.0
    odd = collect(1:2:2count); even = odd .+ 1
    A = sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(2.0,count),fill(term,count),fill(6.0,count),fill(5.0,count)),2count,2count)
    problem = LinearProblem(A,[isodd(i) ? 2ratio : old_cost for i in 1:2count];objective_constant=7.0,
        row_lower=Union{Nothing,Float64}[isodd(i) ? rhs : nothing for i in 1:2count],
        row_upper=[isodd(i) ? rhs : 20.0 for i in 1:2count],
        column_lower=Union{Nothing,Float64}[isodd(i) ? 1.0 : nothing for i in 1:2count],
        column_upper=Union{Nothing,Float64}[isodd(i) ? 3.0 : nothing for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

    for (kind,limit) in ((:positive,53300),(:negative,53300),(:unit_positive,51000),(:unit_negative,51500),(:nonzero_cost,54300),(:zero_ratio,45400))
        problem,pass=aggregation_zero_retained_cost_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
        result=pass(problem)
        ratio=problem.objective[1]/2;old=problem.objective[2]
        @test size(result.problem.A)==(256,128)
        @test result.problem.objective==fill(old-3ratio,128)
        @test result.problem.objective_constant==7+512ratio
        @test JSimplex.postsolve_primal(result,zeros(128))==repeat([2.0,0.0],128)
    end
end
