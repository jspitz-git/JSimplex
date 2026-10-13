using SparseArrays

@testset "Zero bounds shift exactly across numeric types" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), negative in (false,true), amount in (0,1,-1,1//2,-1//2,1//3,-1//3)
        bound = Bound(negative ? -zero(T) : zero(T))
        shift = JSimplex._exact_rational(amount)
        result = JSimplex._shift_bound_exact(T,bound,shift)
        if iszero(amount)
            @test result === bound
        elseif denominator(amount) == 3 && T != Rational{BigInt}
            @test isnothing(result)
        else
            @test JSimplex._exact_rational(JSimplex.bound_value(result)) == -shift
        end
        @test iszero(JSimplex.bound_value(bound))
        @test isnothing(result) || result isa Bound{T}
    end
end

@testset "Zero shifts and unbounded endpoints retain their original bounds" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), amount in (0,1//3,-1)
        bound = JSimplex._unbounded_bound(T)
        @test JSimplex._shift_bound_exact(T,bound,JSimplex._exact_rational(amount)) === bound
    end
    for direction in (-1,1), ambient in (32,64)
        bound = setprecision(BigFloat,256) do
            Bound(BigFloat(7)+direction*BigFloat(2)^(-200))
        end
        setprecision(BigFloat,ambient) do
            @test JSimplex._shift_bound_exact(BigFloat,bound,zero(Rational{BigInt})) === bound
            @test precision(JSimplex.bound_value(bound)) == 256
        end
    end
end

@testset "Zero-bound shortcuts retain exact rejection and tiny shifts" begin
    for kind in (:tiny_bound,:unrepresentable_shift,:tiny_shift), direction in (-1,1), ambient in (32,64)
        bound,shift = setprecision(BigFloat,256) do
            tiny = direction*BigFloat(2)^(-200)
            bound = Bound(kind == :tiny_bound ? tiny : BigFloat(0))
            amount = kind == :tiny_bound ? BigFloat(1) : kind == :tiny_shift ? tiny : BigFloat(1)+tiny
            bound,JSimplex._exact_rational(amount)
        end
        original = JSimplex._exact_rational(JSimplex.bound_value(bound))
        setprecision(BigFloat,ambient) do
            result = JSimplex._shift_bound_exact(BigFloat,bound,shift)
            @test kind == :tiny_shift ? JSimplex._exact_rational(JSimplex.bound_value(result)) == -shift : isnothing(result)
            @test JSimplex._exact_rational(JSimplex.bound_value(bound)) == original
            @test precision(JSimplex.bound_value(bound)) == 256
        end
    end
end

@testset "Zero endpoints preserve all bound-shifting reductions" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:basic,:doubleton,:sparse), coefficient in (2,-2), endpoint in (:lower,:upper,:both)
        lower = endpoint in (:lower,:both) ? T(0) : T(-10)
        upper = endpoint in (:upper,:both) ? T(0) : T(10)
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

@testset "Unrepresentable zero-bound shifts reject all three reductions" begin
    for T in (Float32,Float64), direction in (-1,1), kind in (:basic,:doubleton,:sparse)
        tiny = direction*nextfloat(zero(T))
        if kind == :basic
            problem = LinearProblem(sparse(T[tiny 0; 0 1]),T[0,2];
                row_lower=[T(0),nothing],row_upper=T[0,10],
                column_lower=T[1/2,0],column_upper=T[1/2,10])
            pass = JSimplex._presolve_basic
        else
            problem = LinearProblem(sparse(T[2 1; tiny 0]),T[0,2];
                row_lower=[T(1),nothing],row_upper=T[1,0],
                column_lower=[nothing,T(0)],column_upper=[nothing,T(10)])
            pass = kind == :doubleton ? JSimplex.substitute_free_doubleton : JSimplex.aggregate_sparse_equalities
        end
        original = deepcopy(problem)
        result = pass(problem)
        @test result.problem === problem
        @test isempty(result.postsolve_stack)
        @test problem.A.nzval == original.A.nzval && problem.row_upper == original.row_upper
    end
end

@testset "Presolve passes avoid converting and subtracting zero bounds" begin
function zero_bound_shift_probe(kind; count=128)
    coefficient = kind in (:basic_negative,:sparse_negative) ? -2.0 : 2.0
    if kind in (:basic_positive,:basic_negative,:nonzero_bound)
        A = hcat(sparse(1:count,1:count,fill(coefficient,count),count,count),sparse(ones(count,1)))
        problem = LinearProblem(A,vcat(zeros(count),2.0);objective_constant=7.0,
            row_lower=fill(kind == :nonzero_bound ? 1.0 : 0.0,count),row_upper=fill(10.0,count),
            column_lower=vcat(fill(2.0,count),nothing),column_upper=vcat(fill(2.0,count),nothing))
        return problem,JSimplex._presolve_basic
    elseif kind == :doubleton
        A = sparse(hcat(vcat(2.0,fill(2.0,count)),vcat(1.0,fill(3.0,count))))
        problem = LinearProblem(A,[0.0,2.0];objective_constant=7.0,
            row_lower=vcat(4.0,zeros(count)),row_upper=vcat(4.0,fill(10.0,count)),
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        return problem,JSimplex.substitute_free_doubleton
    end
    odd = collect(1:2:2count); even = odd .+ 1
    A = sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(2.0,count),ones(count),fill(coefficient,count),fill(3.0,count)),2count,2count)
    problem = LinearProblem(A,[isodd(i) ? 0.0 : 2.0 for i in 1:2count];objective_constant=7.0,
        row_lower=[isodd(i) ? 4.0 : 0.0 for i in 1:2count],
        row_upper=[isodd(i) ? 4.0 : 10.0 for i in 1:2count],
        column_lower=Union{Nothing,Float64}[isodd(i) ? 1.0 : nothing for i in 1:2count],
        column_upper=Union{Nothing,Float64}[isodd(i) ? 3.0 : nothing for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

    for (kind,limit) in ((:basic_positive,14_350),(:basic_negative,14_350),
                         (:sparse_positive,47_750),(:sparse_negative,48_250),
                         (:doubleton,17_900),(:nonzero_bound,15_850))
        problem,pass = zero_bound_shift_probe(kind)
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
        expected_lower = (kind == :nonzero_bound ? 1.0 : 0.0)-2coefficient
        @test all(JSimplex.bound_value(result.problem.row_lower[i]) == expected_lower &&
            JSimplex.bound_value(result.problem.row_upper[i]) == 10-2coefficient for i in rows)
    end
end
