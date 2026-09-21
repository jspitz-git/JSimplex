using SparseArrays

@testset "Unit cost products preserve aggregation objectives and projections" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), ratio in (-3,-1,0,1,3), term in (-3,-1,1,3), implied in (false,true)
        problem = LinearProblem(sparse(T[2 term;6 5]),T[2ratio,5];objective_constant=T(7),
            row_lower=T[4,-100],row_upper=T[4,100],
            column_lower=[implied ? nothing : T(1),nothing],column_upper=[implied ? nothing : T(3),nothing])
        original = deepcopy(problem)
        result = JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A) == (implied ? 1 : 2,1)
        @test result.problem.objective == T[5-ratio*term]
        @test result.problem.objective_constant == T(7+4ratio)
        @test result.problem.A[end,1] == T(5-3term)
        @test JSimplex.bound_value(result.problem.row_lower[end]) == -112 && JSimplex.bound_value(result.problem.row_upper[end]) == 88
        x = JSimplex.postsolve_primal(result,T[2])
        @test x == T[2-term,2]
        @test sum(problem.objective.*x)+problem.objective_constant == 2only(result.problem.objective)+result.problem.objective_constant
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Unit cost products use committed costs across candidates" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), ratios in ((1,-1),(-1,3),(3,-3),(0,1)), terms in ((3,-1),(1,-1))
        r1,r2=ratios; t1,t2=terms
        problem = LinearProblem(sparse(T[2 0 t1;0 2 t2;2 2 5]),T[2r1,2r2,5];objective_constant=T(7),
            row_lower=[T(4),T(4),nothing],row_upper=T[4,4,20],
            column_lower=fill(nothing,3),column_upper=fill(nothing,3))
        original = deepcopy(problem)
        result = JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A) == (1,1)
        @test result.problem.objective == T[5-r1*t1-r2*t2]
        @test result.problem.objective_constant == T(7+4r1+4r2)
        @test result.problem.A[1,1] == T(5-t1-t2)
        @test JSimplex.postsolve_primal(result,T[2]) == T[2-t1,2-t2,2]
        @test isequal(problem.objective,original.objective) && isequal(problem.A.nzval,original.A.nzval)
    end
end

@testset "Cost products distinguish exact units from high-precision neighbors" begin
    for mode in (:exact,:near_ratio,:near_term,:tail,:cancel), ambient in (32,64,256), direction in (-1,1)
        problem = setprecision(BigFloat,256) do
            epsilon=BigFloat(2)^(-200)
            ratio=direction*(BigFloat(1)+(mode in (:near_ratio,:tail,:cancel) ? epsilon : zero(BigFloat)))
            term=BigFloat(3)+(mode == :near_term ? epsilon : zero(BigFloat))
            old=mode == :tail ? BigFloat(3direction) : mode == :cancel ? ratio*term : BigFloat(5)
            # Explicit zero in the pivot column keeps its degree at two while
            # avoiding unrelated precision rejection in the matrix update.
            A=sparse([1,2,1,2],[1,1,2,2],BigFloat[2,0,term,5],2,2)
            LinearProblem(A,BigFloat[2ratio,old];objective_constant=BigFloat(7),
                row_lower=[BigFloat(0),nothing],row_upper=[BigFloat(0),nothing],
                column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        saved_cost=JSimplex._exact_rational.(problem.objective)
        saved_matrix=JSimplex._exact_rational.(problem.A.nzval)
        expected=saved_cost[2]-saved_cost[1]/2*JSimplex._exact_rational(problem.A[1,2])
        setprecision(BigFloat,ambient) do
            result=JSimplex.aggregate_sparse_equalities(problem)
            if mode in (:near_ratio,:near_term) && ambient < 256
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            else
                @test size(result.problem.A) == (1,1)
                @test JSimplex._exact_rational(only(result.problem.objective)) == expected
                @test precision(only(result.problem.objective)) == ambient
                @test result.problem.objective_constant == 7
            end
            @test JSimplex._exact_rational.(problem.objective) == saved_cost
            @test JSimplex._exact_rational.(problem.A.nzval) == saved_matrix
        end
    end
end

@testset "Unit cost products retain large non-dyadic rational arithmetic" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), direction in (-1,1), side in (:ratio,:term)
        value=T((BigInt(1)<<300)+1,BigInt(den))
        ratio,term=side == :ratio ? (T(direction),value) : (value,T(direction))
        problem=LinearProblem(sparse(T[2 term;2 5]),T[2ratio,5];objective_constant=T(7),
            row_lower=[T(0),nothing],row_upper=[T(0),nothing],
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original=deepcopy(problem)
        result=JSimplex.aggregate_sparse_equalities(problem)
        expected=5-ratio*term
        @test size(result.problem.A)==(1,1)
        @test only(result.problem.objective)==expected
        @test gcd(numerator(only(result.problem.objective)),denominator(only(result.problem.objective)))==1
        @test result.problem.objective_constant==7
        @test JSimplex.postsolve_primal(result,T[0])==T[0,0]
        @test problem.objective==original.objective && problem.A.nzval==original.A.nzval
    end
end

@testset "Unit cost products retain representability rejection" begin
    for T in (Float32,Float64), direction in (-1,1), mode in (:overflow,:half_subnormal)
        cost=mode == :overflow ? T(direction) : T(direction)*nextfloat(zero(T))
        term=mode == :overflow ? floatmax(T) : T(1)
        old=mode == :overflow ? -T(direction)*floatmax(T) : zero(T)
        A=sparse([1,2,1,2],[1,1,2,2],T[mode == :overflow ? 1 : 2,0,term,5],2,2)
        problem=LinearProblem(A,T[cost,old];row_lower=[T(0),nothing],row_upper=[T(0),nothing],
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original=deepcopy(problem)
        result=JSimplex.aggregate_sparse_equalities(problem)
        # A second pivot can be representable; compare the exact reduced
        # objective through restoration instead of assuming identity.
        x=JSimplex.postsolve_primal(result,zeros(T,size(result.problem.A,2)))
        @test isempty(result.postsolve_stack) || all(record.column != 1 for record in only(result.postsolve_stack).records)
        @test all(isfinite,result.problem.objective)
        @test sum(JSimplex._exact_rational.(problem.objective).*JSimplex._exact_rational.(x))==JSimplex._exact_rational(result.problem.objective_constant)
        @test isequal(problem.objective,original.objective) && isequal(problem.A.nzval,original.A.nzval)
    end
end

@testset "Sparse aggregation avoids unit cost-product multiplication" begin
function aggregation_unit_cost_product_probe(kind; count=128)
    ratio = kind == :ratio_positive ? 1.0 : kind == :ratio_negative ? -1.0 : kind == :zero_ratio ? 0.0 : 3.0
    term = kind == :term_positive ? 1.0 : kind == :term_negative ? -1.0 : 3.0
    odd = collect(1:2:2count); even = odd .+ 1
    A = sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(2.0,count),fill(term,count),fill(6.0,count),fill(5.0,count)),2count,2count)
    problem = LinearProblem(A,[isodd(i) ? 2ratio : 5.0 for i in 1:2count];objective_constant=7.0,
        row_lower=Union{Nothing,Float64}[isodd(i) ? 4.0 : nothing for i in 1:2count],
        row_upper=[isodd(i) ? 4.0 : 20.0 for i in 1:2count],
        column_lower=Union{Nothing,Float64}[isodd(i) ? 1.0 : nothing for i in 1:2count],
        column_upper=Union{Nothing,Float64}[isodd(i) ? 3.0 : nothing for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

    for (kind,limit) in ((:ratio_positive,53400),(:ratio_negative,53500),(:term_positive,52300),(:term_negative,52600),(:nonunit,54300),(:zero_ratio,46600))
        problem,pass=aggregation_unit_cost_product_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
        result=pass(problem)
        ratio=problem.objective[1]/2;term=problem.A[1,2]
        @test size(result.problem.A)==(256,128)
        @test result.problem.objective==fill(5-ratio*term,128)
        @test result.problem.objective_constant==7+512ratio
        @test JSimplex.postsolve_primal(result,zeros(128))==repeat([2.0,0.0],128)
    end
end
