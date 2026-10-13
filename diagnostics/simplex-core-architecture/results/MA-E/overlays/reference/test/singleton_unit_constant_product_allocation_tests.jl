using SparseArrays

@testset "Singleton unit products preserve constants and projections" begin
    cases=((-1,4),(1,4),(3,-1),(3,1),(-1,-1),(1,1),(-3,-1),(-3,1),(0,4),(3,0),(3,4),(1//2,-1))
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), (ratio,rhs) in cases, bounded in (false,true)
        problem=LinearProblem(sparse(T[2 3;0 1]),T[2ratio,5];objective_constant=T(7),
            row_lower=[T(rhs),nothing],row_upper=[T(rhs),nothing],
            column_lower=[bounded ? one(T) : nothing,nothing],column_upper=[bounded ? T(3) : nothing,nothing])
        original=deepcopy(problem);result=JSimplex.aggregate_singleton_equalities(problem)
        @test result.problem.A==reshape(T[3,1],2,1)
        @test result.problem.objective_constant==T(7+ratio*rhs)
        @test result.problem.objective==T[5-3ratio]
        @test result.problem.row_lower==[Bound{T}(bounded ? T(rhs-6) : nothing),Bound{T}(nothing)]
        @test result.problem.row_upper==[Bound{T}(bounded ? T(rhs-2) : nothing),Bound{T}(nothing)]
        restored=JSimplex.postsolve_primal(result,T[2])
        @test restored==T[(rhs-6)/2,2]
        @test problem.objective_constant+sum(problem.objective.*restored)==result.problem.objective_constant+2only(result.problem.objective)
        @test isequal(problem.objective_constant,original.objective_constant) && isequal(problem.objective,original.objective)
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower)
    end
end

@testset "Singleton unit products accumulate committed constants" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), ratios in ((1,-1,3),(-1,3,-3),(0,1,-1)), rhs_values in ((4,-1,1),(1,-1,0)), initial in (0,7)
        prices=T[ratios...];rhs=T[rhs_values...]
        A=hcat(sparse(1:3,1:3,fill(T(2),3),3,3),sparse(ones(T,3,1)))
        problem=LinearProblem(A,[2prices;T(2)];objective_constant=T(initial),row_lower=rhs,row_upper=rhs,
            column_lower=fill(nothing,4),column_upper=fill(nothing,4))
        original=deepcopy(problem);result=JSimplex.aggregate_singleton_equalities(problem)
        @test result.problem.A==ones(T,3,1)
        @test result.problem.objective_constant==T(initial)+sum(prices.*rhs)
        @test result.problem.objective==T[2-sum(prices)]
        restored=JSimplex.postsolve_primal(result,T[2])
        @test restored==[(rhs.-2)./2;T(2)]
        @test problem.objective_constant+sum(problem.objective.*restored)==result.problem.objective_constant+2only(result.problem.objective)
        basis=JSimplex.Basis(collect(2:4),[JSimplex.AT_UPPER;fill(JSimplex.BASIC,3)])
        restored_basis=JSimplex.restore_basis(result,basis)
        @test restored_basis.basic_indices==collect(1:3) && restored_basis.states[4]==JSimplex.AT_UPPER
        @test isequal(problem.objective,original.objective) && isequal(problem.row_lower,original.row_lower)
    end
end

@testset "Singleton constant products distinguish stored unit neighbors" begin
    for side in (:ratio,:rhs), mode in (:exact,:near,:tail,:cancel), ambient in (32,64,256), direction in (-1,1)
        problem=setprecision(BigFloat,256) do
            epsilon=BigFloat(2)^(-200)
            unit=direction*(BigFloat(1)+(mode==:exact ? zero(BigFloat) : epsilon))
            ratio,rhs=side==:ratio ? (unit,BigFloat(3)) : (BigFloat(3),unit)
            initial=mode==:tail ? BigFloat(-3direction) : mode==:cancel ? -ratio*rhs : BigFloat(7)
            LinearProblem(sparse(BigFloat[2 1;0 1]),BigFloat[2ratio,ratio];objective_constant=initial,
                row_lower=[rhs,nothing],row_upper=[rhs,nothing],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        saved_cost=JSimplex._exact_rational.(problem.objective)
        saved_constant=JSimplex._exact_rational(problem.objective_constant)
        saved_rhs=JSimplex._exact_rational(bound_value(problem.row_lower[1]))
        expected=saved_constant+saved_cost[1]/2*saved_rhs
        setprecision(BigFloat,ambient) do
            result=JSimplex.aggregate_singleton_equalities(problem)
            if mode==:near && ambient<256
                @test result.problem===problem && isempty(result.postsolve_stack)
            else
                @test result.problem.A==ones(BigFloat,2,1)
                @test JSimplex._exact_rational(result.problem.objective_constant)==expected
                @test precision(result.problem.objective_constant)==ambient
                @test result.problem.objective==BigFloat[0]
                @test iszero(expected) ? isequal(result.problem.objective_constant,zero(BigFloat)) : true
            end
            @test JSimplex._exact_rational.(problem.objective)==saved_cost
            @test JSimplex._exact_rational(problem.objective_constant)==saved_constant
            @test JSimplex._exact_rational(bound_value(problem.row_lower[1]))==saved_rhs
            @test precision(problem.objective_constant)==256
        end
    end
end

@testset "Singleton unit products preserve non-dyadic rationals" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), direction in (-1,1), side in (:ratio,:rhs)
        value=T((BigInt(1)<<300)+1,BigInt(den))
        ratio,rhs=side==:ratio ? (T(direction),value) : (value,T(direction))
        problem=LinearProblem(sparse(T[2 1;0 1]),T[2ratio,ratio];objective_constant=T(7),
            row_lower=[rhs,nothing],row_upper=[rhs,nothing],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original=deepcopy(problem);result=JSimplex.aggregate_singleton_equalities(problem)
        @test result.problem.objective_constant==7+ratio*rhs
        @test denominator(result.problem.objective_constant)>0 && gcd(numerator(result.problem.objective_constant),denominator(result.problem.objective_constant))==1
        @test result.problem.objective==T[0]
        @test JSimplex.postsolve_primal(result,T[0])==T[rhs/2,0]
        derived=result.problem.objective_constant+T(2,3)
        @test derived==original.objective_constant+ratio*rhs+T(2,3)
        result.problem.objective[1]+=1;result.problem.A.nzval[1]+=1
        @test isequal(problem.objective_constant,original.objective_constant) && isequal(problem.objective,original.objective) && isequal(problem.A.nzval,original.A.nzval)
    end
end

@testset "Singleton aggregation avoids signed-unit constant multiplication" begin
function singleton_unit_constant_product_probe(kind; count=128, T=Float64)
    ratio=kind==:ratio_positive ? one(T) : kind==:ratio_negative ? -one(T) : T(3)
    rhs=kind==:rhs_positive ? one(T) : kind==:rhs_negative ? -one(T) : kind==:zero_rhs ? zero(T) : T(4)
    A=hcat(sparse(1:count,1:count,fill(T(2),count),count,count),sparse(ones(T,count,1)))
    problem=LinearProblem(A,[fill(2ratio,count);T(2)];objective_constant=T(7),
        row_lower=fill(rhs,count),row_upper=fill(rhs,count),
        column_lower=[ones(T,count);nothing],column_upper=[fill(T(3),count);nothing])
    return problem,JSimplex.aggregate_singleton_equalities
end
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:ratio_positive,:ratio_negative,:rhs_positive,:rhs_negative,:nonunit,:zero_rhs)
        count=4;problem,pass=singleton_unit_constant_product_probe(kind;count,T)
        original=deepcopy(problem);result=pass(problem)
        ratio=problem.objective[1]/2;rhs=bound_value(problem.row_upper[1])
        @test result.problem.A==ones(T,count,1)
        @test result.problem.row_lower==fill(Bound(rhs-6),count)
        @test result.problem.row_upper==fill(Bound(rhs-2),count)
        @test result.problem.objective==T[2-count*ratio]
        @test result.problem.objective_constant==T(7)+count*ratio*rhs
        primal=T[rhs-4];restored=JSimplex.postsolve_primal(result,primal)
        @test restored==[fill(T(2),count);only(primal)]
        @test problem.objective_constant+sum(problem.objective.*restored)==result.problem.objective_constant+sum(result.problem.objective.*primal)
        m,n=size(result.problem.A)
        for state in (JSimplex.AT_LOWER,JSimplex.AT_UPPER)
            basis=JSimplex.Basis(collect(n+1:n+m),[fill(state,n);fill(JSimplex.BASIC,m)])
            restored_basis=JSimplex.restore_basis(result,basis)
            @test restored_basis.basic_indices==collect(1:count)
            @test restored_basis.states[count+1]==state
        end
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective)
        @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
        @test isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
    for (kind,limit) in ((:ratio_positive,26600),(:ratio_negative,26600),(:rhs_positive,26600),(:rhs_negative,26600),(:nonunit,27400),(:zero_rhs,23400))
        problem,pass=singleton_unit_constant_product_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
