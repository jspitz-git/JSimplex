using SparseArrays

@testset "Equal-denominator aggregation preserves matrix updates and projections" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), multiplier in (-3,-1,1,3), term in (1,1//2), mode in (:nonzero,:cancel,:unequal,:zero), implied in (false,true)
        product = T(multiplier)*T(term)
        old = mode == :nonzero ? product-T(2term) : mode == :cancel ? product : mode == :unequal ? product/T(2) : zero(T)
        problem = LinearProblem(sparse(T[2 term;2multiplier old]),T[0,2];objective_constant=T(7),
            row_lower=T[4,-100],row_upper=T[4,100],
            column_lower=[implied ? nothing : T(1),nothing],
            column_upper=[implied ? nothing : T(3),nothing])
        original = deepcopy(problem)
        result = JSimplex.aggregate_sparse_equalities(problem)
        expected = old-product
        @test size(result.problem.A) == (implied ? 1 : 2,1)
        @test result.problem.A[end,1] == expected
        @test nnz(result.problem.A) == (implied ? 0 : 1)+!iszero(expected)
        @test !iszero(expected) || !signbit(result.problem.A[end,1])
        @test result.problem.objective == T[2] && result.problem.objective_constant == T(7)
        @test JSimplex.bound_value(result.problem.row_lower[end]) == -100-4multiplier && JSimplex.bound_value(result.problem.row_upper[end]) == 100-4multiplier
        @test JSimplex.postsolve_primal(result,T[2]) == T[2-term,2]
        @test isequal(problem.A.nzval,original.A.nzval) && problem.A.colptr == original.A.colptr && problem.A.rowval == original.A.rowval && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Equal-denominator aggregation subtracts from committed updates" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), old in (1//2,3//2,5//2,7//2)
        problem = LinearProblem(sparse(T[2 0 1;0 2 1;3 3 old]),T[0,0,2];objective_constant=T(7),
            row_lower=[T(4),T(4),nothing],row_upper=T[4,4,20],
            column_lower=fill(nothing,3),column_upper=fill(nothing,3))
        original = deepcopy(problem)
        result = JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A) == (1,1)
        @test result.problem.A[1,1] == T(old-3)
        @test JSimplex.bound_value(result.problem.row_upper[1]) == T(8)
        @test result.problem.objective == T[2] && result.problem.objective_constant == T(7)
        @test JSimplex.postsolve_primal(result,T[2]) == T[1,1,2]
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Aggregation denominator shortcut preserves stored BigFloat precision" begin
    for mode in (:exact,:cancel,:tail,:nonrepresentable), ambient in (32,64,256), direction in (-1,1)
        problem = setprecision(BigFloat,256) do
            epsilon = BigFloat(2)^(-200)
            coefficient = BigFloat(3)+(mode == :exact ? zero(BigFloat) : epsilon)
            old = mode == :exact ? BigFloat(5) : mode == :cancel ? coefficient : mode == :tail ? BigFloat(3)-epsilon : BigFloat(5)-epsilon
            LinearProblem(sparse(BigFloat[1 1;direction*coefficient direction*old]),BigFloat[0,2];objective_constant=BigFloat(7),
                row_lower=[zero(BigFloat),nothing],row_upper=[zero(BigFloat),nothing],
                column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        original_entries = JSimplex._exact_rational.(problem.A.nzval)
        expected = JSimplex._exact_rational(problem.A[2,2])-JSimplex._exact_rational(problem.A[2,1])
        setprecision(BigFloat,ambient) do
            result = JSimplex.aggregate_sparse_equalities(problem)
            if mode == :nonrepresentable && ambient < 256
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            else
                @test size(result.problem.A) == (1,1)
                @test JSimplex._exact_rational(result.problem.A[1,1]) == expected
                @test all(precision(v) == ambient for v in result.problem.A.nzval)
                @test nnz(result.problem.A) == !iszero(expected)
            end
            @test JSimplex._exact_rational.(problem.A.nzval) == original_entries
        end
    end
end

@testset "Aggregation canonicalizes large non-dyadic differences" begin
    T = Rational{BigInt}
    for den in (5,7,15,21), factor in (-2,-1,1,2,4)
        coefficient = T((BigInt(1)<<300)+1,BigInt(den))
        old = factor*coefficient
        problem = LinearProblem(sparse(T[1 1;coefficient old]),T[0,2];
            row_lower=[T(0),nothing],row_upper=[T(0),nothing],
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original = deepcopy(problem.A.nzval)
        result = JSimplex.aggregate_sparse_equalities(problem)
        expected = old-coefficient
        @test size(result.problem.A) == (1,1)
        @test result.problem.A[1,1] == expected && denominator(result.problem.A[1,1]) == denominator(expected)
        @test gcd(numerator(result.problem.A[1,1]),denominator(result.problem.A[1,1])) == 1
        @test nnz(result.problem.A) == !iszero(expected)
        @test JSimplex.postsolve_primal(result,T[2]) == T[-2,2]
        @test problem.A.nzval == original
    end
end

@testset "Aggregation matrix rejection preserves source storage" begin
    for T in (Float32,Float64), direction in (-1,1), mode in (:overflow,:half_subnormal)
        value = T(direction)*(mode == :overflow ? floatmax(T) : nextfloat(zero(T)))
        pivot,term,old = mode == :overflow ? (T(1),T(1),-value) : (T(2),T(3),value)
        problem = LinearProblem(sparse(T[pivot term;value old]),T[0,3];
            row_lower=[zero(T),nothing],row_upper=[zero(T),nothing],
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original = deepcopy(problem)
        result = JSimplex.aggregate_sparse_equalities(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test isequal(problem.A.nzval,original.A.nzval) && problem.A.colptr == original.A.colptr && problem.A.rowval == original.A.rowval
    end
end

@testset "Aggregation equal matrix denominator allocation guards" begin
function aggregation_equal_matrix_denominator_probe(kind; count=128)
    fractional = kind in (:fraction_positive,:fraction_negative,:unequal_denominator,:cancellation)
    direction = kind in (:integer_negative,:fraction_negative) ? -1.0 : 1.0
    term = direction * (fractional ? 0.5 : 1.0)
    old = kind == :unequal_denominator ? 1.0 : kind == :cancellation ? 1.5 :
        direction * (fractional ? 0.5 : 5.0)
    odd = collect(1:2:2count); even = odd .+ 1
    A = sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(2.0,count),fill(term,count),fill(6.0,count),fill(old,count)),2count,2count)
    problem = LinearProblem(A,[isodd(i) ? 0.0 : 2.0 for i in 1:2count];objective_constant=7.0,
        row_lower=Union{Nothing,Float64}[isodd(i) ? 4.0 : nothing for i in 1:2count],
        row_upper=[isodd(i) ? 4.0 : 20.0 for i in 1:2count],
        column_lower=Union{Nothing,Float64}[isodd(i) ? 1.0 : nothing for i in 1:2count],
        column_upper=Union{Nothing,Float64}[isodd(i) ? 3.0 : nothing for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

    for (kind,limit) in ((:integer_positive,45350),(:integer_negative,45650),(:fraction_positive,46480),(:fraction_negative,46480),(:unequal_denominator,46800),(:cancellation,45400))
        problem,pass = aggregation_equal_matrix_denominator_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        result = pass(problem)
        expected = problem.A[2,2]-3problem.A[1,2]
        @test size(result.problem.A) == (256,128)
        @test all(result.problem.A[2i,i] == expected && JSimplex.bound_value(result.problem.row_upper[2i]) == 8 for i in 1:128)
        @test nnz(result.problem.A) == 128+128*!iszero(expected)
        @test result.problem.objective == fill(2.0,128) && result.problem.objective_constant == 7.0
        @test JSimplex.postsolve_primal(result,zeros(128)) == repeat([2.0,0.0],128)
    end
end
