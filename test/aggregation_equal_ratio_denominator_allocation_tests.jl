using SparseArrays

@testset "Equal ratio denominators preserve objective rounding policy" begin
    for T in (Float32,Float64), sparse_pass in (false,true), direction in (-1,1), price in (-1,1)
        coefficient=T(3direction)
        A=sparse(T[coefficient 1; (sparse_pass ? coefficient : 0) (sparse_pass ? 0 : 1)])
        problem=LinearProblem(A,T[price,0];objective_constant=T(7),
            row_lower=[zero(T),nothing],row_upper=[zero(T),nothing],
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original=deepcopy(problem)
        pass=sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
        result=pass(problem)
        if sparse_pass
            @test result.problem === problem && isempty(result.postsolve_stack)
        else
            @test size(result.problem.A)==(2,1)
            @test result.problem.objective==T[-T(price)/coefficient]
            @test result.problem.objective_constant==7
            @test JSimplex.postsolve_primal(result,T[0])==T[0,0]
        end
        @test isequal(problem.objective,original.objective) && isequal(problem.A.nzval,original.A.nzval)
    end
end

@testset "Shared objective ratio denominators preserve stored precision" begin
    for sparse_pass in (false,true), fractional in (false,true), mode in (:exact,:inexact), ambient in (32,64,256), direction in (-1,1)
        problem=setprecision(BigFloat,256) do
            coefficient=direction*(fractional ? (BigFloat(2)^200+1)/BigFloat(2)^201 : BigFloat(2)^200)
            price=3abs(coefficient)
            mode==:inexact && (price+=fractional ? BigFloat(2)^(-200) : one(BigFloat))
            LinearProblem(sparse(BigFloat[coefficient 1; (sparse_pass ? coefficient : 0) (sparse_pass ? 0 : 1)]),BigFloat[price,0];
                objective_constant=BigFloat(7),row_lower=[BigFloat(0),nothing],row_upper=[BigFloat(0),nothing],
                column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        original=deepcopy(problem);exact_price=JSimplex._exact_rational(problem.objective[1]);exact_coefficient=JSimplex._exact_rational(problem.A[1,1])
        expected=-exact_price/exact_coefficient
        pass=sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
        setprecision(BigFloat,ambient) do
            result=pass(problem)
            if mode==:inexact && (fractional || ambient<256)
                @test result.problem === problem && isempty(result.postsolve_stack)
            else
                @test JSimplex._exact_rational(only(result.problem.objective))==expected
                @test precision(only(result.problem.objective))==ambient
                @test result.problem.objective_constant==7
                @test size(result.problem.A)==(sparse_pass ? 1 : 2,1)
                @test JSimplex.postsolve_primal(result,BigFloat[0])==BigFloat[0,0]
            end
            @test JSimplex._exact_rational(problem.objective[1])==exact_price
            @test JSimplex._exact_rational(problem.A[1,1])==exact_coefficient
            @test precision(problem.objective[1])==256
            @test isequal(problem.objective,original.objective) && isequal(problem.A.nzval,original.A.nzval)
        end
    end
end

@testset "Large rational objective ratios preserve canonical signs" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), direction in (-1,1), price_sign in (-1,1), sparse_pass in (false,true)
        value=(BigInt(1)<<300)+1
        coefficient=direction*T(value,BigInt(den));price=price_sign*T(value+2,BigInt(den))
        problem=LinearProblem(sparse(T[coefficient 1; (sparse_pass ? coefficient : 0) (sparse_pass ? 0 : 1)]),T[price,0];
            objective_constant=T(7),row_lower=[zero(T),nothing],row_upper=[zero(T),nothing],
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original=deepcopy(problem)
        pass=sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
        result=pass(problem);cost=only(result.problem.objective)
        @test cost == -price/coefficient
        @test denominator(cost)>0 && gcd(numerator(cost),denominator(cost))==1
        @test result.problem.objective_constant==7
        restored=JSimplex.postsolve_primal(result,T[2])
        @test restored==T[-2/coefficient,2]
        @test sum(problem.objective.*restored)==2cost
        @test isequal(problem.objective,original.objective) && isequal(problem.A.nzval,original.A.nzval)
    end
end

@testset "Aggregation avoids general equal-denominator objective division" begin
function aggregation_equal_ratio_denominator_probe(kind; count=128, T=Float64)
    name=string(kind)
    sparse_pass=startswith(name,"sparse")
    direction=endswith(name,"negative") ? -1 : 1
    fractional=occursin("fraction",name)
    coefficient=T(direction)*(fractional ? T(1)/2 : T(2))
    price=fractional || kind==:unequal_denominator ? T(3)/2 : T(6)
    kind==:unit_coefficient && (coefficient=one(T))
    rhs=T(4direction)
    A=hcat(sparse(1:count,1:count,fill(coefficient,count),count,count),sparse(ones(T,count,1)))
    lower=Union{Nothing,T}[rhs for _ in 1:count];upper=fill(rhs,count)
    if sparse_pass
        A=vcat(A,sparse(reshape([ones(T,count);T(2)],1,count+1)))
        push!(lower,nothing);push!(upper,T(1000))
    end
    problem=LinearProblem(A,[fill(price,count);T(2)];objective_constant=T(7),
        row_lower=lower,row_upper=upper,
        column_lower=[ones(T,count);nothing],column_upper=[fill(T(3),count);nothing])
    return problem,sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
end
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:singleton_integer_positive,:singleton_integer_negative,:singleton_fraction_positive,:singleton_fraction_negative,:sparse_integer_positive,:sparse_integer_negative,:sparse_fraction_positive,:sparse_fraction_negative,:unequal_denominator,:unit_coefficient)
        count=4;problem,pass=aggregation_equal_ratio_denominator_probe(kind;count,T)
        original=deepcopy(problem);result=pass(problem)
        sparse_pass=startswith(string(kind),"sparse")
        coefficient=problem.A[1,1];price=problem.objective[1];rhs=bound_value(problem.row_upper[1])
        low=min(rhs-coefficient,rhs-3coefficient);high=max(rhs-coefficient,rhs-3coefficient)
        expected_matrix=sparse_pass ? [ones(T,count);T(2)-count/coefficient] : ones(T,count)
        @test result.problem.A==reshape(expected_matrix,:,1)
        expected_lower=sparse_pass ? [fill(Bound(low),count);Bound{T}(nothing)] : fill(Bound(low),count)
        expected_upper=sparse_pass ? [fill(Bound(high),count);Bound(T(1000)-count*rhs/coefficient)] : fill(Bound(high),count)
        @test result.problem.row_lower==expected_lower
        @test result.problem.row_upper==expected_upper
        @test result.problem.objective==T[T(2)-count*price/coefficient]
        @test result.problem.objective_constant==T(7)+count*price*rhs/coefficient
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
    for (kind,limit) in ((:singleton_integer_positive,27400),(:singleton_integer_negative,27400),(:singleton_fraction_positive,27900),(:singleton_fraction_negative,27900),(:sparse_integer_positive,43350),(:sparse_integer_negative,43360),(:sparse_fraction_positive,43700),(:sparse_fraction_negative,43710),(:unequal_denominator,27800),(:unit_coefficient,25600))
        problem,pass=aggregation_equal_ratio_denominator_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
