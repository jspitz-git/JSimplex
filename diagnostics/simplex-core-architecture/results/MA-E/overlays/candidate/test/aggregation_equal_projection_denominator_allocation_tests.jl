using SparseArrays

@testset "Projection differences preserve exact values and earlier shortcuts" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        for (coefficient,value,rhs) in ((2,1,5),(2,3,5),(-2,1,-5),(-2,3,-5),
            (1//2,1,5//2),(1//2,3,5//2),(-1//2,1,-5//2),(-1//2,3,-5//2),
            (1//3,2,5//3),(1//3,2,7//3),(1,2,0),(2,2,4),(2,0,5),(1,2,9//4))
            exact_rhs,pivot=Rational{BigInt}(rhs),Rational{BigInt}(coefficient)
            bound=Bound(T(value));saved=deepcopy((exact_rhs,pivot,bound))
            expected=exact_rhs-pivot*JSimplex._exact_rational(T(value))
            represented=JSimplex._represent_exact(T,expected)
            projected=JSimplex._project_equality_bound(T,exact_rhs,pivot,bound)
            @test isnothing(represented) ? isnothing(projected) : projected==Bound(represented)
            @test isequal((exact_rhs,pivot,bound),saved)
            if !isnothing(projected)
                @test JSimplex._exact_rational(bound_value(projected))==expected
            end
        end
        @test JSimplex._project_equality_bound(T,big(5)//2,big(1)//2,Bound{T}(nothing))==Bound{T}(nothing)
        @test JSimplex._project_equality_bound(T,big(5)//2,big(1)//2,Bound(-zero(T)))==Bound(T(5//2))
    end
end

@testset "Large rational projection differences remain canonical" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), direction in (-1,1), coefficient in (-1,1), delta in (0,1,2,5)
        value=direction*T((BigInt(1)<<300)+1,BigInt(den));pivot=T(coefficient)
        rhs=pivot*value+T(delta,den);bound=Bound(value);saved=deepcopy((rhs,pivot,bound))
        projected=JSimplex._project_equality_bound(T,rhs,pivot,bound)
        @test bound_value(projected)==T(delta,den)
        @test gcd(numerator(bound_value(projected)),denominator(bound_value(projected)))==1
        @test isequal((rhs,pivot,bound),saved)
    end
end

@testset "Shared projection denominators preserve stored precision gates" begin
    for sparse_pass in (false,true), mode in (:exact,:inexact), ambient in (32,64,256), direction in (-1,1)
        problem=setprecision(BigFloat,256) do
            epsilon=BigFloat(2)^(-200)
            rhs=direction*(BigFloat(3)+(mode==:exact ? epsilon : 3epsilon))
            LinearProblem(sparse(BigFloat[direction 1; (sparse_pass ? 1 : 0) (sparse_pass ? 0 : 1)]),zeros(BigFloat,2);
                row_lower=[rhs,nothing],row_upper=[rhs,nothing],
                column_lower=[BigFloat(1)+epsilon,nothing],column_upper=[nothing,nothing])
        end
        original=deepcopy(problem)
        exact_rhs=JSimplex._exact_rational(bound_value(problem.row_lower[1]))
        expected=direction*(big(2)+(mode==:exact ? big(0)//1 : big(2)//big(2)^200))
        pass=sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
        setprecision(BigFloat,ambient) do
            projected=JSimplex._project_equality_bound(BigFloat,exact_rhs,big(direction)//1,problem.column_lower[1])
            result=pass(problem)
            if mode==:inexact && ambient<256
                @test isnothing(projected)
                @test result.problem === problem && isempty(result.postsolve_stack)
            else
                @test JSimplex._exact_rational(bound_value(projected))==expected
                endpoint=direction>0 ? result.problem.row_upper[1] : result.problem.row_lower[1]
                @test JSimplex._exact_rational(bound_value(endpoint))==expected
                @test precision(bound_value(endpoint))==ambient
                @test size(result.problem.A)==(2,1)
                restored=setprecision(BigFloat,256) do
                    JSimplex.postsolve_primal(result,BigFloat[0])
                end
                @test JSimplex._exact_rational.(restored)==[exact_rhs/direction,big(0)//1]
            end
            @test JSimplex._exact_rational(bound_value(problem.row_lower[1]))==exact_rhs
            @test precision(bound_value(problem.column_lower[1]))==256
            @test isequal(problem.column_lower,original.column_lower) && isequal(problem.row_upper,original.row_upper)
        end
    end
end

@testset "Aggregation avoids general equal-denominator projection subtraction" begin
function aggregation_equal_projection_denominator_probe(kind; count=128, T=Float64)
    name=string(kind)
    sparse_pass=startswith(name,"sparse")
    direction=endswith(name,"negative") ? -1 : 1
    fractional=occursin("fraction",name) || kind==:unequal_denominator
    coefficient=T(direction)*(fractional ? T(1)/2 : T(2))
    rhs=T(direction)*(fractional ? T(5)/2 : T(5))
    kind==:unequal_denominator && (rhs=T(9)/4)
    kind==:zero_rhs && (rhs=zero(T))
    A=hcat(sparse(1:count,1:count,fill(coefficient,count),count,count),sparse(ones(T,count,1)))
    lower=Union{Nothing,T}[rhs for _ in 1:count];upper=fill(rhs,count)
    if sparse_pass
        A=vcat(A,sparse(reshape([ones(T,count);T(2)],1,count+1)))
        push!(lower,nothing);push!(upper,T(1000))
    end
    problem=LinearProblem(A,[ones(T,count);T(2)];objective_constant=T(7),
        row_lower=lower,row_upper=upper,
        column_lower=[ones(T,count);nothing],column_upper=[fill(T(3),count);nothing])
    return problem,sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
end

    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:singleton_integer_positive,:singleton_integer_negative,:singleton_fraction_positive,:singleton_fraction_negative,:sparse_integer_positive,:sparse_integer_negative,:sparse_fraction_positive,:sparse_fraction_negative,:unequal_denominator,:zero_rhs)
        count=4;problem,pass=aggregation_equal_projection_denominator_probe(kind;count,T)
        original=deepcopy(problem);result=pass(problem)
        sparse_pass=startswith(string(kind),"sparse")
        coefficient=problem.A[1,1];rhs=bound_value(problem.row_upper[1])
        low=min(rhs-coefficient,rhs-3coefficient);high=max(rhs-coefficient,rhs-3coefficient)
        expected_matrix=sparse_pass ? [ones(T,count);T(2)-count/coefficient] : ones(T,count)
        @test result.problem.A==reshape(expected_matrix,:,1)
        expected_lower=sparse_pass ? [fill(Bound(low),count);Bound{T}(nothing)] : fill(Bound(low),count)
        expected_upper=sparse_pass ? [fill(Bound(high),count);Bound(T(1000)-count*rhs/coefficient)] : fill(Bound(high),count)
        @test result.problem.row_lower==expected_lower
        @test result.problem.row_upper==expected_upper
        @test result.problem.objective==T[T(2)-count/coefficient]
        @test result.problem.objective_constant==T(7)+count*rhs/coefficient
        primal=T[rhs-2coefficient];restored=JSimplex.postsolve_primal(result,primal)
        @test restored==[fill(T(2),count);only(primal)]
        @test problem.objective_constant+sum(problem.objective.*restored)==result.problem.objective_constant+sum(result.problem.objective.*primal)
        m,n=size(result.problem.A)
        for state in (JSimplex.AT_LOWER,JSimplex.AT_UPPER)
            basis=JSimplex.Basis(collect(n+1:n+m),[fill(state,n);fill(JSimplex.BASIC,m)])
            restored_basis=JSimplex.restore_basis(result,basis)
            @test restored_basis.basic_indices==(sparse_pass ? [collect(1:count);2count+2] : collect(1:count))
            @test restored_basis.states[count+1]==state
        end
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective)
        @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
        @test isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
    for (kind,limit) in ((:singleton_integer_positive,27800),(:singleton_integer_negative,27800),(:singleton_fraction_positive,27800),(:singleton_fraction_negative,27800),(:sparse_integer_positive,44050),(:sparse_integer_negative,44070),(:sparse_fraction_positive,43600),(:sparse_fraction_negative,43610),(:unequal_denominator,28100),(:zero_rhs,25900))
        problem,pass=aggregation_equal_projection_denominator_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
