using SparseArrays

@testset "Nonunit multiplier division preserves stored zero coefficients" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), pivot in (2,-2,1//2,-1//2), bounded in (false,true)
        A=sparse([1,1,2,2],[1,2,1,2],T[pivot,1,0,4],2,2)
        problem=LinearProblem(A,T[0,2];objective_constant=T(7),
            row_lower=[T(4),bounded ? T(-10) : nothing],row_upper=[T(4),bounded ? T(20) : nothing],
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original=deepcopy(problem);result=JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A)==(1,1)
        @test only(result.problem.A)==4
        @test result.problem.row_lower==[bounded ? Bound(T(-10)) : Bound{T}(nothing)]
        @test result.problem.row_upper==[bounded ? Bound(T(20)) : Bound{T}(nothing)]
        @test result.problem.objective==T[2] && result.problem.objective_constant==7
        @test JSimplex.postsolve_primal(result,T[4])==T[0,4]
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Shared multiplier denominators preserve stored precision gates" begin
    for fractional in (false,true), mode in (:exact,:inexact), ambient in (32,64,256), direction in (-1,1)
        problem=setprecision(BigFloat,256) do
            pivot=direction*(fractional ? (BigFloat(2)^200+1)/BigFloat(2)^201 : BigFloat(2)^200)
            coefficient=3abs(pivot)
            mode==:inexact && (coefficient+=fractional ? BigFloat(2)^(-200) : one(BigFloat))
            LinearProblem(sparse(BigFloat[pivot 1;coefficient 0]),BigFloat[0,2];
                objective_constant=BigFloat(7),row_lower=[BigFloat(0),nothing],row_upper=BigFloat[0,100],
                column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        original=deepcopy(problem)
        saved=JSimplex._exact_rational.(problem.A.nzval)
        expected=-JSimplex._exact_rational(problem.A[2,1])/JSimplex._exact_rational(problem.A[1,1])
        setprecision(BigFloat,ambient) do
            result=JSimplex.aggregate_sparse_equalities(problem)
            if mode==:inexact && (fractional || ambient<256)
                @test result.problem === problem && isempty(result.postsolve_stack)
            else
                @test size(result.problem.A)==(1,1)
                @test JSimplex._exact_rational(only(result.problem.A))==expected
                @test precision(only(result.problem.A.nzval))==ambient
                @test bound_value(only(result.problem.row_upper))==100
                @test JSimplex.postsolve_primal(result,BigFloat[0])==BigFloat[0,0]
            end
            @test JSimplex._exact_rational.(problem.A.nzval)==saved
            @test all(precision(x)==256 for x in problem.A.nzval)
            @test isequal(problem.row_upper,original.row_upper) && isequal(problem.objective,original.objective)
        end
    end
end

@testset "Large rational multipliers retain canonical signs and row values" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), direction in (-1,1), coefficient_sign in (-1,1)
        value=(BigInt(1)<<300)+1
        pivot=direction*T(value,BigInt(den));coefficient=coefficient_sign*T(value+2,BigInt(den))
        problem=LinearProblem(sparse(T[pivot 1;coefficient 0]),T[0,2];objective_constant=T(7),
            row_lower=[zero(T),nothing],row_upper=T[0,20],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original=deepcopy(problem);result=JSimplex.aggregate_sparse_equalities(problem)
        entry=only(result.problem.A)
        @test entry == -coefficient/pivot
        @test denominator(entry)>0 && gcd(numerator(entry),denominator(entry))==1
        @test result.problem.objective==T[2] && result.problem.objective_constant==7
        restored=JSimplex.postsolve_primal(result,T[2])
        @test restored==T[-2/pivot,2]
        @test (problem.A*restored)[2]==2entry
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Aggregation avoids general equal-denominator multiplier division" begin
function aggregation_equal_multiplier_denominator_probe(kind; count=128, T=Float64)
    name=string(kind)
    direction=endswith(name,"negative") ? -1 : 1
    fractional=startswith(name,"fraction")
    pivot=T(direction)*(fractional ? T(1)/2 : T(2))
    coefficient=fractional || kind==:unequal_denominator ? T(3)/2 : T(6)
    kind==:unit_pivot && (pivot=one(T))
    odd=collect(1:2:2count);even=odd.+1
    A=sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(pivot,count),ones(T,count),fill(coefficient,count),fill(T(5),count)),2count,2count)
    problem=LinearProblem(A,[isodd(i) ? zero(T) : T(2) for i in 1:2count];objective_constant=T(7),
        row_lower=[isodd(i) ? T(4) : nothing for i in 1:2count],
        row_upper=[isodd(i) ? T(4) : T(100) for i in 1:2count],
        column_lower=[isodd(i) ? one(T) : nothing for i in 1:2count],
        column_upper=[isodd(i) ? T(3) : nothing for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:integer_positive,:integer_negative,:fraction_positive,:fraction_negative,:unequal_denominator,:unit_pivot)
        count=4;problem,pass=aggregation_equal_multiplier_denominator_probe(kind;count,T)
        original=deepcopy(problem);result=pass(problem)
        pivot=problem.A[1,1];multiplier=problem.A[2,1]/pivot
        low=min(T(4)-pivot,T(4)-3pivot);high=max(T(4)-pivot,T(4)-3pivot)
        expected_matrix=sparse(collect(1:2count),repeat(collect(1:count),inner=2),repeat(T[1,5-multiplier],count),2count,count)
        @test result.problem.A==expected_matrix
        @test result.problem.row_lower==[isodd(i) ? Bound(low) : Bound{T}(nothing) for i in 1:2count]
        @test result.problem.row_upper==[Bound(isodd(i) ? high : T(100)-4multiplier) for i in 1:2count]
        @test result.problem.objective==fill(T(2),count) && result.problem.objective_constant==7
        primal=fill(T(4)-2pivot,count);restored=JSimplex.postsolve_primal(result,primal)
        @test restored==repeat(T[2,T(4)-2pivot],count)
        @test problem.objective_constant+sum(problem.objective.*restored)==result.problem.objective_constant+sum(result.problem.objective.*primal)
        m,n=size(result.problem.A)
        for state in (JSimplex.AT_LOWER,JSimplex.AT_UPPER)
            basis=JSimplex.Basis(collect(n+1:n+m),[fill(state,n);fill(JSimplex.BASIC,m)])
            restored_basis=JSimplex.restore_basis(result,basis)
            @test restored_basis.basic_indices==[isodd(i) ? i : 2count+i for i in 1:2count]
            @test restored_basis.states[2:2:2count]==fill(state,count)
        end
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective)
        @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
        @test isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
    for (kind,limit) in ((:integer_positive,44500),(:integer_negative,44500),(:fraction_positive,45000),(:fraction_negative,45000),(:unequal_denominator,45300),(:unit_pivot,42700))
        problem,pass=aggregation_equal_multiplier_denominator_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
