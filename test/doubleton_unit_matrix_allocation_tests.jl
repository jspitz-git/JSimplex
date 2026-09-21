using SparseArrays

@testset "Doubleton matrix products reuse signed unit operands" begin
function doubleton_unit_matrix_probe(kind; count=128, T=Float64)
    coefficient = T(kind == :positive_coefficient ? 1 : kind == :negative_coefficient ? -1 : kind == :zero_coefficient ? 0 : 3)
    retained_coefficient = T(kind == :positive_beta ? -2 : kind == :negative_beta ? 2 : 1)
    A = sparse(hcat(vcat(T(2),fill(coefficient,count)),vcat(retained_coefficient,fill(T(2),count))))
    problem = LinearProblem(A,T[2,3];objective_constant=T(7),
        row_lower=vcat(T(4),fill(T(-100),count)),row_upper=vcat(T(4),fill(T(100),count)),
        column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
    return problem,JSimplex.substitute_free_doubleton
end

    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive_coefficient,:negative_coefficient,:positive_beta,:negative_beta,:nonunit,:zero_coefficient), rhs in (0,4), old in (0,2)
        problem,pass = doubleton_unit_matrix_probe(kind;count=4,T)
        problem.row_lower[1] = problem.row_upper[1] = Bound(T(rhs))
        for row in 2:5
            problem.A[row,2] = T(old)
        end
        original = deepcopy(problem)
        result = pass(problem)
        coefficient = problem.A[2,1]
        beta = -problem.A[1,2]/T(2)
        @test size(result.problem.A) == (4,1)
        @test Matrix(result.problem.A) == fill(T(old)+coefficient*beta,4,1)
        @test result.problem.objective == T[3+2beta] && result.problem.objective_constant == T(7+rhs)
        @test all(JSimplex.bound_value(result.problem.row_lower[i]) == T(-100)-coefficient*T(rhs)/T(2) && JSimplex.bound_value(result.problem.row_upper[i]) == T(100)-coefficient*T(rhs)/T(2) for i in 1:4)
        @test JSimplex.postsolve_primal(result,T[2]) == T[T(rhs)/T(2)+2beta,2]
        basis = JSimplex.Basis(collect(2:5),[JSimplex.FREE_NONBASIC;fill(JSimplex.BASIC,4)])
        @test JSimplex.restore_basis(result,basis).basic_indices == [1,4,5,6,7]
        @test all(!iszero,result.problem.A.nzval)
        @test isequal(problem.A.nzval,original.A.nzval) && problem.A.colptr == original.A.colptr && problem.A.rowval == original.A.rowval && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper && problem.objective == original.objective && problem.objective_constant == original.objective_constant
    end
    for (kind,limit) in ((:positive_coefficient,16_200),(:negative_coefficient,16_500),(:positive_beta,17_400),(:negative_beta,17_400),(:nonunit,18_250),(:zero_coefficient,450))
        problem,pass = doubleton_unit_matrix_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end

@testset "Doubleton near-unit matrix coefficients preserve tiny residuals" begin
    for sign in (-1,1), direction in (-1,1), beta in (-1,1), ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            coefficient = BigFloat(sign)+direction*BigFloat(2)^(-200)
            LinearProblem(sparse(BigFloat[2 -2beta; coefficient -sign*beta]),BigFloat[0,3];objective_constant=BigFloat(7),
                row_lower=[BigFloat(4),nothing],row_upper=[BigFloat(4),nothing],
                column_lower=[nothing,BigFloat(-10)],column_upper=[nothing,BigFloat(10)])
        end
        original = JSimplex._exact_rational(problem.A[2,1])
        setprecision(BigFloat,ambient) do
            result = JSimplex.substitute_free_doubleton(problem)
            @test size(result.problem.A) == (1,1)
            @test JSimplex._exact_rational(result.problem.A[1,1]) == beta*(original-sign)
            @test !iszero(result.problem.A[1,1])
            @test JSimplex.postsolve_primal(result,BigFloat[0]) == BigFloat[2,0]
            @test JSimplex._exact_rational(problem.A[2,1]) == original && precision(problem.A[2,1]) == 256
        end
    end
end

@testset "Doubleton near-unit beta retains exact representability checks" begin
    for sign in (-1,1), direction in (-1,1), ambient in (32,64,256)
        problem = setprecision(BigFloat,256) do
            beta = BigFloat(sign)+direction*BigFloat(2)^(-200)
            LinearProblem(sparse(BigFloat[1 -beta; 1 -sign]),BigFloat[0,3];objective_constant=BigFloat(7),
                row_lower=[BigFloat(0),nothing],row_upper=[BigFloat(0),nothing],
                column_lower=[nothing,BigFloat(-10)],column_upper=[nothing,BigFloat(10)])
        end
        original = JSimplex._exact_rational(problem.A[1,2])
        setprecision(BigFloat,ambient) do
            result = JSimplex.substitute_free_doubleton(problem)
            if ambient == 256
                @test size(result.problem.A) == (1,1)
                @test JSimplex._exact_rational(result.problem.A[1,1]) == -original-sign
                @test !iszero(result.problem.A[1,1])
            else
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            end
            @test JSimplex._exact_rational(problem.A[1,2]) == original
        end
    end
end
