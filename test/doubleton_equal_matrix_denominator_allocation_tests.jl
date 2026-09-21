using SparseArrays

@testset "Doubleton equal matrix denominator allocation guards" begin
function doubleton_equal_matrix_denominator_probe(kind; count=128, T=Float64)
    retained_coefficient = T(kind in (:cancel_integer,:sum_integer) ? 2 : 1)
    old_value = kind == :cancel_fraction ? T(3)/2 : kind == :sum_fraction ? T(1)/2 : T(kind == :cancel_integer ? 3 : kind == :sum_integer ? 5 : kind == :zero_old ? 0 : 1)
    A = sparse(vcat(collect(1:count+1),collect(1:count+1)),vcat(fill(1,count+1),fill(2,count+1)),
        vcat(T[2;fill(T(3),count)],T[retained_coefficient;fill(old_value,count)]),count+1,2)
    problem = LinearProblem(A,T[2,3];objective_constant=T(7),
        row_lower=vcat(T(4),fill(nothing,count)),row_upper=vcat(T(4),fill(nothing,count)),
        column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
    return problem,JSimplex.substitute_free_doubleton
end
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:cancel_integer,:cancel_fraction,:sum_integer,:sum_fraction,:unequal_denominator,:zero_old)
        problem,pass = doubleton_equal_matrix_denominator_probe(kind;count=4,T)
        original = deepcopy(problem)
        beta = -problem.A[1,2]/problem.A[1,1]
        expected = problem.A[2,2]+problem.A[2,1]*beta
        result = pass(problem)
        @test size(result.problem.A) == (4,1)
        @test Matrix(result.problem.A) == fill(expected,4,1)
        @test nnz(result.problem.A) == (iszero(expected) ? 0 : 4)
        @test result.problem.objective == T[3+2beta] && result.problem.objective_constant == T(11)
        @test all(!isfinite(result.problem.row_lower[i]) && !isfinite(result.problem.row_upper[i]) for i in 1:4)
        @test JSimplex.postsolve_primal(result,T[2]) == T[2+2beta,2]
        basis = JSimplex.Basis(collect(2:5),[JSimplex.FREE_NONBASIC;fill(JSimplex.BASIC,4)])
        @test JSimplex.restore_basis(result,basis).basic_indices == [1,4,5,6,7]
        @test isequal(problem.A.nzval,original.A.nzval) && problem.A.colptr == original.A.colptr && problem.A.rowval == original.A.rowval && isequal(problem.objective,original.objective) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
    for (kind,limit) in ((:cancel_integer,6100),(:cancel_fraction,6950),(:sum_integer,6500),(:sum_fraction,7380),(:unequal_denominator,7800),(:zero_old,5100))
        problem,pass = doubleton_equal_matrix_denominator_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end

@testset "Equal-denominator matrix sums preserve storage bounds and restoration" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), beta in (-1,-1//2,1//2,1), direction in (-1,1), mode in (:cancel,:same,:partial,:unequal)
        coefficient = T(3direction)
        product = coefficient*T(beta)
        old = mode == :cancel ? -product : mode == :same ? product : mode == :partial ? -product/T(3) : product/T(2)
        problem = LinearProblem(sparse(T[2 -2beta;coefficient old]),T[2,3];objective_constant=T(7),
            row_lower=T[4,-100],row_upper=T[4,100],
            column_lower=Union{Nothing,T}[nothing,T(-10)],column_upper=Union{Nothing,T}[nothing,T(10)])
        original = deepcopy(problem)
        result = JSimplex.substitute_free_doubleton(problem)
        expected = old+product
        @test size(result.problem.A) == (1,1)
        @test result.problem.A[1,1] == expected
        @test nnz(result.problem.A) == (iszero(expected) ? 0 : 1)
        @test !iszero(expected) || !signbit(result.problem.A[1,1])
        @test result.problem.objective == T[3+2beta] && result.problem.objective_constant == T(11)
        @test JSimplex.bound_value(result.problem.row_lower[1]) == -100-2coefficient && JSimplex.bound_value(result.problem.row_upper[1]) == 100-2coefficient
        @test JSimplex.postsolve_primal(result,T[2]) == T[2+2beta,2]
        basis = JSimplex.Basis([2],[JSimplex.FREE_NONBASIC,JSimplex.BASIC])
        @test JSimplex.restore_basis(result,basis).basic_indices == [1,4]
        @test isequal(problem.A.nzval,original.A.nzval) && problem.A.colptr == original.A.colptr && problem.A.rowval == original.A.rowval && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Equal-denominator matrix sums preserve BigFloat precision and cancellation tails" begin
    for mode in (:exact,:cancel,:tail,:nonrepresentable), ambient in (32,64,256), direction in (-1,1)
        problem = setprecision(BigFloat,256) do
            epsilon = BigFloat(2)^(-200)
            coefficient = BigFloat(3)+(mode == :exact ? zero(BigFloat) : epsilon)
            old = mode == :exact ? BigFloat(5) : mode == :cancel ? -coefficient : mode == :tail ? -BigFloat(3)+epsilon : BigFloat(5)+epsilon
            LinearProblem(sparse(BigFloat[2 -2;direction*coefficient direction*old]),BigFloat[0,3];objective_constant=BigFloat(7),
                row_lower=[zero(BigFloat),nothing],row_upper=[zero(BigFloat),nothing],
                column_lower=[nothing,BigFloat(-10)],column_upper=[nothing,BigFloat(10)])
        end
        original_entries = JSimplex._exact_rational.(problem.A.nzval)
        expected = JSimplex._exact_rational(problem.A[2,1])+JSimplex._exact_rational(problem.A[2,2])
        setprecision(BigFloat,ambient) do
            result = JSimplex.substitute_free_doubleton(problem)
            if mode == :nonrepresentable && ambient < 256
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            else
                @test size(result.problem.A) == (1,1)
                @test JSimplex._exact_rational(result.problem.A[1,1]) == expected
                @test all(precision(v) == ambient for v in result.problem.A.nzval)
                @test !iszero(expected) || nnz(result.problem.A) == 0
            end
            @test JSimplex._exact_rational.(problem.A.nzval) == original_entries
        end
    end
end

@testset "Equal-denominator rational matrix entries reduce large non-dyadic sums" begin
    T = Rational{BigInt}
    for denominator_value in (5,7,15,21), factor in (-1,1,2,4)
        coefficient = T((BigInt(1)<<300)+1,BigInt(denominator_value))
        old = factor*coefficient
        problem = LinearProblem(sparse(T[1 -1;coefficient old]),T[0,3];objective_constant=zero(T),
            row_lower=[T(1),nothing],row_upper=[T(1),nothing],
            column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
        saved_entries = deepcopy(problem.A.nzval)
        result = JSimplex.substitute_free_doubleton(problem)
        expected = old+coefficient
        @test size(result.problem.A) == (1,1)
        @test result.problem.A[1,1] == expected && denominator(result.problem.A[1,1]) == denominator(expected)
        @test gcd(numerator(result.problem.A[1,1]),denominator(result.problem.A[1,1])) == 1
        @test nnz(result.problem.A) == (iszero(expected) ? 0 : 1)
        @test JSimplex.postsolve_primal(result,T[2]) == T[3,2]
        @test problem.A.nzval == saved_entries
    end
end

@testset "Matrix representability rejection preserves source storage" begin
    for T in (Float32,Float64), direction in (-1,1), mode in (:overflow,:half_subnormal)
        value = T(direction)*(mode == :overflow ? floatmax(T) : nextfloat(zero(T)))
        pivot,retained = mode == :overflow ? (T(1),T(-1)) : (T(2),T(1))
        problem = LinearProblem(sparse(T[pivot retained;value value]),T[0,3];
            row_lower=[zero(T),nothing],row_upper=[zero(T),nothing],
            column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
        original = deepcopy(problem)
        result = JSimplex.substitute_free_doubleton(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test isequal(problem.A.nzval,original.A.nzval) && problem.A.colptr == original.A.colptr && problem.A.rowval == original.A.rowval
    end
end
