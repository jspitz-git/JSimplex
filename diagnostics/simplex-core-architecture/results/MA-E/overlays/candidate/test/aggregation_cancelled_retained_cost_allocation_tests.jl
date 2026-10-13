using SparseArrays

@testset "Cancelled retained costs preserve objectives and projections" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), ratio in (-3,-1,-1//2,1//2,1,3), term in (-3,-1,1,3), implied in (false,true)
        problem=LinearProblem(sparse(T[2 term;6 5]),T[2ratio,ratio*term];objective_constant=T(7),
            row_lower=T[4,-100],row_upper=T[4,100],
            column_lower=[implied ? nothing : T(1),nothing],column_upper=[implied ? nothing : T(3),nothing])
        original=deepcopy(problem)
        result=JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A)==(implied ? 1 : 2,1)
        @test isequal(only(result.problem.objective),zero(T))
        @test result.problem.objective_constant==T(7+4ratio)
        @test result.problem.A[end,1]==T(5-3term)
        @test JSimplex.bound_value(result.problem.row_lower[end])==-112 && JSimplex.bound_value(result.problem.row_upper[end])==88
        x=JSimplex.postsolve_primal(result,T[2])
        @test x==T[2-term,2]
        @test sum(problem.objective.*x)+problem.objective_constant==result.problem.objective_constant
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Cost cancellation uses the currently committed objective" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), ratios in ((1,1),(1,-1),(-1,3),(0,1)), old in (0,3,6,9)
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

@testset "High-precision costs cancel exactly without losing tiny residuals" begin
    for side in (:ratio,:term), mode in (:cancel,:tail,:inexact), ambient in (32,64,256), direction in (-1,1)
        problem=setprecision(BigFloat,256) do
            epsilon=BigFloat(2)^(-200)
            value=direction*(BigFloat(3)+epsilon)
            ratio,term=side==:ratio ? (value,BigFloat(1)) : (BigFloat(1),value)
            product=ratio*term
            old=mode==:cancel ? product : mode==:tail ? product-direction*2epsilon : product+BigFloat(2)+epsilon
            A=sparse([1,2,1],[1,1,2],BigFloat[2,0,term],2,2)
            LinearProblem(A,BigFloat[2ratio,old];objective_constant=BigFloat(7),
                row_lower=[BigFloat(0),nothing],row_upper=[BigFloat(0),nothing],
                column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        saved_cost=JSimplex._exact_rational.(problem.objective)
        saved_matrix=JSimplex._exact_rational.(problem.A.nzval)
        expected=saved_cost[2]-saved_cost[1]/2*JSimplex._exact_rational(problem.A[1,2])
        setprecision(BigFloat,ambient) do
            result=JSimplex.aggregate_sparse_equalities(problem)
            if mode==:inexact && ambient<256
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            else
                @test size(result.problem.A)==(1,1)
                @test JSimplex._exact_rational(only(result.problem.objective))==expected
                @test precision(only(result.problem.objective))==ambient
                @test mode==:cancel ? !signbit(only(result.problem.objective)) : !iszero(only(result.problem.objective))
            end
            @test JSimplex._exact_rational.(problem.objective)==saved_cost
            @test JSimplex._exact_rational.(problem.A.nzval)==saved_matrix
        end
    end
end

@testset "Adjacent floating costs are not treated as cancellation" begin
    for T in (Float32,Float64), ratio in (-3,-1,1,3), direction in (-1,1)
        product=T(3ratio);old=direction>0 ? nextfloat(product) : prevfloat(product)
        problem=LinearProblem(sparse(T[2 3;2 5]),T[2ratio,old];objective_constant=T(7),
            row_lower=[T(0),nothing],row_upper=[T(0),nothing],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        result=JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A)==(1,1)
        @test only(result.problem.objective)==old-product
        @test !iszero(only(result.problem.objective))
        @test problem.objective==T[2ratio,old]
    end
end

@testset "Non-dyadic rational costs cancel to canonical zero" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), direction in (-1,1), side in (:ratio,:term)
        value=T((BigInt(1)<<300)+1,BigInt(den))
        ratio,term=side==:ratio ? (value,T(direction)) : (T(direction),value)
        problem=LinearProblem(sparse(T[2 term;2 5]),T[2ratio,ratio*term];objective_constant=T(7),
            row_lower=[T(0),nothing],row_upper=[T(0),nothing],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original=deepcopy(problem)
        result=JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A)==(1,1)
        @test only(result.problem.objective)==zero(T)
        @test numerator(only(result.problem.objective))==0 && denominator(only(result.problem.objective))==1
        @test result.problem.objective_constant==7
        @test JSimplex.postsolve_primal(result,T[0])==T[0,0]
        @test problem.objective==original.objective && problem.A.nzval==original.A.nzval
    end
end

@testset "Sparse aggregation avoids subtraction of identical retained costs" begin
function aggregation_cancelled_retained_cost_probe(kind; count=128)
    ratio = kind == :unit_positive ? 1.0 : kind == :unit_negative ? -1.0 : kind == :negative ? -3.0 : 3.0
    rhs = 4.0
    term = 3.0
    old_cost = kind == :unequal ? 5.0 : kind == :zero_old ? 0.0 : ratio*term
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

    for (kind,limit) in ((:positive,53000),(:negative,53000),(:unit_positive,50700),(:unit_negative,51200),(:unequal,54300),(:zero_old,53000))
        problem,pass=aggregation_cancelled_retained_cost_probe(kind)
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
