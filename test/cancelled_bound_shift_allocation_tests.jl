using SparseArrays

@testset "Equal stored bounds and exact shifts cancel across numeric types" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), amount in (0,-0.0,1,-1,1//2,-1//2,1//3,-1//3)
        bound = Bound(T(amount))
        original = JSimplex._exact_rational(JSimplex.bound_value(bound))
        result = JSimplex._shift_bound_exact(T,bound,original)
        @test iszero(JSimplex.bound_value(result))
        @test iszero(original) ? result === bound : result isa Bound{T}
        @test JSimplex._exact_rational(JSimplex.bound_value(bound)) == original
    end
end

@testset "Exact bound cancellation preserves high-precision distinctions" begin
    for kind in (:equal,:near), sign in (-1,1), direction in (-1,1), ambient in (32,64)
        bound = setprecision(BigFloat,256) do
            Bound(BigFloat(3sign)+direction*BigFloat(2)^(-200))
        end
        original = JSimplex._exact_rational(JSimplex.bound_value(bound))
        shift = kind == :equal ? original : JSimplex._exact_rational(3sign)
        expected = original-shift
        setprecision(BigFloat,ambient) do
            result = JSimplex._shift_bound_exact(BigFloat,bound,shift)
            @test JSimplex._exact_rational(JSimplex.bound_value(result)) == expected
            @test kind == :equal ? iszero(JSimplex.bound_value(result)) : !iszero(JSimplex.bound_value(result))
            @test JSimplex._exact_rational(JSimplex.bound_value(bound)) == original
            @test precision(JSimplex.bound_value(bound)) == 256
        end
    end
end

@testset "Adjacent floating bounds do not count as exact cancellation" begin
    for T in (Float32,Float64), sign in (-1,1), direction in (-1,1)
        shift = T(3sign)
        value = direction > 0 ? nextfloat(shift) : prevfloat(shift)
        bound = Bound(value)
        result = JSimplex._shift_bound_exact(T,bound,JSimplex._exact_rational(shift))
        @test JSimplex.bound_value(result) == value-shift
        @test !iszero(JSimplex.bound_value(result))
        @test JSimplex.bound_value(bound) == value
    end
end

@testset "Cancelled endpoints preserve all bound-shifting reductions" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:basic,:doubleton,:sparse), coefficient in (2,-2), endpoint in (:lower,:upper,:both)
        lower = T(2coefficient)+(endpoint in (:lower,:both) ? T(0) : T(-10))
        upper = T(2coefficient)+(endpoint in (:upper,:both) ? T(0) : T(10))
        if kind == :basic
            problem = LinearProblem(sparse(reshape(T[coefficient,1],1,2)),T[0,2];objective_constant=T(7),
                row_lower=T[lower],row_upper=T[upper],column_lower=[T(2),nothing],column_upper=[T(2),nothing])
            pass = JSimplex._presolve_basic
        else
            problem = LinearProblem(sparse(T[2 1; coefficient 3]),T[0,2];objective_constant=T(7),
                row_lower=T[4,lower],row_upper=T[4,upper],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
            pass = kind == :doubleton ? JSimplex.substitute_free_doubleton : JSimplex.aggregate_sparse_equalities
        end
        original = deepcopy(problem)
        result = pass(problem)
        @test size(result.problem.A) == (1,1)
        @test JSimplex.bound_value(result.problem.row_lower[1]) == lower-T(2coefficient)
        @test JSimplex.bound_value(result.problem.row_upper[1]) == upper-T(2coefficient)
        @test result.problem.A[1,1] == T(kind == :basic ? 1 : 3-coefficient/2)
        @test result.problem.objective == T[2] && result.problem.objective_constant == T(7)
        @test JSimplex.postsolve_primal(result,T[0]) == T[2,0]
        @test problem.A.nzval == original.A.nzval && problem.row_lower == original.row_lower && problem.row_upper == original.row_upper
    end
end

@testset "All bound-shifting passes preserve tiny nonzero residuals" begin
    for kind in (:basic,:doubleton,:sparse), coefficient in (2,-2), direction in (-1,1), ambient in (32,64)
        problem = setprecision(BigFloat,256) do
            lower = BigFloat(2coefficient)+direction*BigFloat(2)^(-200)
            if kind == :basic
                LinearProblem(sparse(reshape(BigFloat[coefficient,1],1,2)),BigFloat[0,2];objective_constant=BigFloat(7),
                    row_lower=[lower],row_upper=BigFloat[10],column_lower=[BigFloat(2),nothing],column_upper=[BigFloat(2),nothing])
            else
                LinearProblem(sparse(BigFloat[2 1; coefficient 3]),BigFloat[0,2];objective_constant=BigFloat(7),
                    row_lower=[BigFloat(4),lower],row_upper=BigFloat[4,10],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
            end
        end
        original = JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[end]))
        pass = kind == :basic ? JSimplex._presolve_basic : kind == :doubleton ? JSimplex.substitute_free_doubleton : JSimplex.aggregate_sparse_equalities
        setprecision(BigFloat,ambient) do
            result = pass(problem)
            @test size(result.problem.A) == (1,1)
            @test JSimplex._exact_rational(JSimplex.bound_value(result.problem.row_lower[1])) == original-2coefficient
            @test !iszero(JSimplex.bound_value(result.problem.row_lower[1]))
            @test JSimplex.postsolve_primal(result,BigFloat[0]) == BigFloat[2,0]
            @test JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[end])) == original
        end
    end
end

@testset "Presolve passes avoid subtracting identical exact bounds" begin
function cancelled_bound_shift_probe(kind; count=128)
    coefficient = kind in (:basic_negative,:sparse_negative) ? -2.0 : 2.0
    if kind in (:basic_positive,:basic_negative,:unequal_bound)
        A = hcat(sparse(1:count,1:count,fill(coefficient,count),count,count),sparse(ones(count,1)))
        problem = LinearProblem(A,vcat(zeros(count),2.0);objective_constant=7.0,
            row_lower=fill(kind == :unequal_bound ? 1.0 : 2coefficient,count),row_upper=fill(10.0,count),
            column_lower=vcat(fill(2.0,count),nothing),column_upper=vcat(fill(2.0,count),nothing))
        return problem,JSimplex._presolve_basic
    elseif kind == :doubleton
        A = sparse(hcat(vcat(2.0,fill(2.0,count)),vcat(1.0,fill(3.0,count))))
        problem = LinearProblem(A,[0.0,2.0];objective_constant=7.0,
            row_lower=fill(4.0,count+1),row_upper=vcat(4.0,fill(10.0,count)),
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        return problem,JSimplex.substitute_free_doubleton
    end
    odd = collect(1:2:2count); even = odd .+ 1
    A = sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(2.0,count),ones(count),fill(coefficient,count),fill(3.0,count)),2count,2count)
    problem = LinearProblem(A,[isodd(i) ? 0.0 : 2.0 for i in 1:2count];objective_constant=7.0,
        row_lower=[isodd(i) ? 4.0 : 2coefficient for i in 1:2count],
        row_upper=[isodd(i) ? 4.0 : 10.0 for i in 1:2count],
        column_lower=Union{Nothing,Float64}[isodd(i) ? 1.0 : nothing for i in 1:2count],
        column_upper=Union{Nothing,Float64}[isodd(i) ? 3.0 : nothing for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

    for (kind,limit) in ((:basic_positive,14_850),(:basic_negative,14_850),
                         (:sparse_positive,48_250),(:sparse_negative,48_750),
                         (:doubleton,18_400),(:unequal_bound,15_850))
        problem,pass = cancelled_bound_shift_probe(kind)
        pass(problem)
        measured = @timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        result = pass(problem)
        coefficient = kind in (:basic_negative,:sparse_negative) ? -2.0 : 2.0
        is_sparse = kind in (:sparse_positive,:sparse_negative)
        @test result.problem.objective == fill(2.0,is_sparse ? 128 : 1)
        @test result.problem.objective_constant == 7.0
        if is_sparse
            @test JSimplex.postsolve_primal(result,ones(128)) == repeat([1.5,1.0],128)
        elseif kind == :doubleton
            @test JSimplex.postsolve_primal(result,[1.0]) == [1.5,1.0]
        else
            @test JSimplex.postsolve_primal(result,[5-2coefficient]) == vcat(fill(2.0,128),5-2coefficient)
        end
        rows = is_sparse ? (2:2:256) : axes(result.problem.A,1)
        expected_lower = kind == :unequal_bound ? 1.0-2coefficient : 0.0
        @test all(JSimplex.bound_value(result.problem.row_lower[i]) == expected_lower &&
            JSimplex.bound_value(result.problem.row_upper[i]) == 10-2coefficient for i in rows)
    end
end
