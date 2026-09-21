using SparseArrays

@testset "Doubleton skips exact addition to zero matrix entries" begin
function doubleton_zero_old_matrix_probe(kind; count=128, T=Float64)
    coefficient = T(kind in (:absent_negative,:stored_negative) ? -3 : kind == :zero_coefficient ? 0 : 3)
    stored = kind in (:stored_positive,:stored_negative,:nonzero,:zero_coefficient)
    second_rows = stored ? collect(1:count+1) : [1]
    old_value = kind in (:nonzero,:zero_coefficient) ? T(2) : kind == :stored_negative ? -zero(T) : zero(T)
    A = sparse(vcat(collect(1:count+1),second_rows),vcat(fill(1,count+1),fill(2,length(second_rows))),
        vcat(T[2;fill(coefficient,count)],stored ? T[1;fill(old_value,count)] : T[1]),count+1,2)
    problem = LinearProblem(A,T[2,3];objective_constant=T(7),
        row_lower=vcat(T(4),fill(T(-100),count)),row_upper=vcat(T(4),fill(T(100),count)),
        column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
    return problem,JSimplex.substitute_free_doubleton
end

    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:absent_positive,:absent_negative,:stored_positive,:stored_negative,:nonzero,:zero_coefficient), rhs in (0,4)
        problem,pass = doubleton_zero_old_matrix_probe(kind;count=4,T)
        problem.row_lower[1] = problem.row_upper[1] = Bound(T(rhs))
        original = deepcopy(problem)
        result = pass(problem)
        coefficient = problem.A[2,1]
        old_value = problem.A[2,2]
        @test nnz(problem.A) == (kind in (:absent_positive,:absent_negative) ? 6 : 10)
        @test size(result.problem.A) == (4,1)
        @test Matrix(result.problem.A) == fill(old_value-coefficient/T(2),4,1)
        @test result.problem.objective == T[2] && result.problem.objective_constant == T(7+rhs)
        @test all(JSimplex.bound_value(result.problem.row_lower[i]) == T(-100)-coefficient*T(rhs)/T(2) && JSimplex.bound_value(result.problem.row_upper[i]) == T(100)-coefficient*T(rhs)/T(2) for i in 1:4)
        @test JSimplex.postsolve_primal(result,T[2]) == T[(T(rhs)-T(2))/T(2),2]
        basis = JSimplex.Basis(collect(2:5),[JSimplex.FREE_NONBASIC;fill(JSimplex.BASIC,4)])
        @test JSimplex.restore_basis(result,basis).basic_indices == [1,4,5,6,7]
        @test isequal(problem.A.nzval,original.A.nzval) && problem.A.colptr == original.A.colptr && problem.A.rowval == original.A.rowval && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper && problem.objective == original.objective && problem.objective_constant == original.objective_constant
    end
    for (kind,limit) in ((:absent_positive,17_000),(:absent_negative,17_000),(:stored_positive,17_000),(:stored_negative,17_000),(:nonzero,18_250),(:zero_coefficient,1_650))
        problem,pass = doubleton_zero_old_matrix_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
    end
end

@testset "Doubleton retains tiny nonzero old matrix entries" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), direction in (-1,1), ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            tiny = T in (Float32,Float64) ? direction*nextfloat(zero(T)) : T(direction*(BigInt(1)//(BigInt(1)<<200)))
            LinearProblem(sparse(T[1 1; tiny 2tiny]),T[0,3];objective_constant=T(7),
                row_lower=[T(0),nothing],row_upper=[T(0),nothing],
                column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
        end
        original = JSimplex._exact_rational(problem.A[2,2])
        setprecision(BigFloat,ambient) do
            result = JSimplex.substitute_free_doubleton(problem)
            @test size(result.problem.A) == (1,1)
            @test JSimplex._exact_rational(result.problem.A[1,1]) == original/2
            @test !iszero(result.problem.A[1,1])
            @test JSimplex._exact_rational(problem.A[2,2]) == original
        end
    end
end

@testset "Doubleton zero old entries retain product representability checks" begin
    for T in (Float32,Float64), direction in (-1,1), stored in (false,true)
        tiny = direction*nextfloat(zero(T))
        rows = stored ? [1,2,1,2] : [1,2,1]
        columns = stored ? [1,1,2,2] : [1,1,2]
        values = stored ? T[2,tiny,1,0] : T[2,tiny,1]
        problem = LinearProblem(sparse(rows,columns,values,2,2),T[0,3];
            row_lower=[T(0),nothing],row_upper=[T(0),nothing],
            column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
        original = deepcopy(problem)
        result = JSimplex.substitute_free_doubleton(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test isequal(problem.A.nzval,original.A.nzval) && problem.A.colptr == original.A.colptr && problem.A.rowval == original.A.rowval
    end
end

@testset "Doubleton tiny old coefficients prevent inexact matrix updates" begin
    for T in (Float32,Float64,BigFloat), direction in (-1,1), ambient in (32,64,256)
        problem = setprecision(BigFloat,256) do
            tiny = T in (Float32,Float64) ? direction*nextfloat(zero(T)) : BigFloat(direction)*BigFloat(2)^(-200)
            LinearProblem(sparse(T[1 1; 2 tiny]),T[0,3];
                row_lower=[T(0),nothing],row_upper=[T(0),nothing],
                column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
        end
        original = JSimplex._exact_rational(problem.A[2,2])
        setprecision(BigFloat,ambient) do
            result = JSimplex.substitute_free_doubleton(problem)
            if T == BigFloat && ambient == 256
                @test size(result.problem.A) == (1,1)
                @test JSimplex._exact_rational(result.problem.A[1,1]) == original-2
            else
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            end
            @test JSimplex._exact_rational(problem.A[2,2]) == original
        end
    end
end
