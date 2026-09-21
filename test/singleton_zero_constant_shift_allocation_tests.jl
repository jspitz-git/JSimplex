using SparseArrays

@testset "Singleton zero RHS preserves constant and projected bounds" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), ratio in (-3,-1,-1//2,1//2,1,3), negative_zero in (false,true), fixed_bounds in (false,true)
        rhs=negative_zero ? -zero(T) : zero(T)
        initial=negative_zero ? -zero(T) : T(7)
        problem=LinearProblem(sparse(T[2 1;0 1]),T[2ratio,5];objective_constant=initial,
            row_lower=[rhs,nothing],row_upper=[rhs,nothing],
            column_lower=[fixed_bounds ? one(T) : nothing,nothing],
            column_upper=[fixed_bounds ? T(3) : nothing,nothing])
        original=deepcopy(problem);result=JSimplex.aggregate_singleton_equalities(problem)
        @test result.problem.A==ones(T,2,1)
        @test result.problem.objective==T[5-ratio]
        @test isequal(result.problem.objective_constant,negative_zero ? zero(T) : T(7))
        @test result.problem.row_lower==[Bound{T}(fixed_bounds ? T(-6) : nothing),Bound{T}(nothing)]
        @test result.problem.row_upper==[Bound{T}(fixed_bounds ? T(-2) : nothing),Bound{T}(nothing)]
        primal=T[-4];restored=JSimplex.postsolve_primal(result,primal)
        @test restored==T[2,-4]
        @test initial+sum(problem.objective.*restored)==result.problem.objective_constant+sum(result.problem.objective.*primal)
        @test isequal(problem.objective_constant,original.objective_constant)
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective)
        @test isequal(problem.row_lower,original.row_lower) && isequal(problem.column_upper,original.column_upper)
    end
end

@testset "Singleton zero shifts preserve previously committed constants" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), rhs_values in ((4,0,-2),(0,4,0),(-2,0,4)), ratios in ((-3,1,3),(1,-1,0),(1//2,-1//2,2))
        rhs=T[rhs_values...];prices=T[ratios...]
        A=hcat(sparse(1:3,1:3,fill(T(2),3),3,3),sparse(ones(T,3,1)))
        problem=LinearProblem(A,[2prices;T(2)];objective_constant=T(7),row_lower=rhs,row_upper=rhs,
            column_lower=fill(nothing,4),column_upper=fill(nothing,4))
        original=deepcopy(problem);result=JSimplex.aggregate_singleton_equalities(problem)
        @test result.problem.A==ones(T,3,1)
        @test result.problem.objective_constant==T(7)+sum(prices.*rhs)
        @test result.problem.objective==T[2-sum(prices)]
        @test all(!isfinite,result.problem.row_lower) && all(!isfinite,result.problem.row_upper)
        primal=T[2];restored=JSimplex.postsolve_primal(result,primal)
        @test restored==[(rhs.-2)./2;T(2)]
        @test problem.objective_constant+sum(problem.objective.*restored)==result.problem.objective_constant+sum(result.problem.objective.*primal)
        basis=JSimplex.Basis(collect(2:4),[JSimplex.AT_LOWER;fill(JSimplex.BASIC,3)])
        restored_basis=JSimplex.restore_basis(result,basis)
        @test restored_basis.basic_indices==collect(1:3)
        @test restored_basis.states[4]==JSimplex.AT_LOWER
        @test isequal(problem.objective,original.objective) && isequal(problem.row_lower,original.row_lower)
    end
end

@testset "Unchanged singleton constant still requires exact representation" begin
    for extended in (false,true), ambient in (32,64,256), ratio in (-3,3)
        problem=setprecision(BigFloat,256) do
            initial=BigFloat(7)+(extended ? BigFloat(2)^(-200) : zero(BigFloat))
            LinearProblem(sparse(BigFloat[2 1;0 1]),BigFloat[2ratio,5];objective_constant=initial,
                row_lower=[BigFloat(0),nothing],row_upper=[BigFloat(0),nothing],
                column_lower=[BigFloat(1),nothing],column_upper=[BigFloat(3),nothing])
        end
        original=deepcopy(problem);exact=JSimplex._exact_rational(problem.objective_constant)
        setprecision(BigFloat,ambient) do
            result=JSimplex.aggregate_singleton_equalities(problem)
            if extended && ambient<256
                @test result.problem===problem && isempty(result.postsolve_stack)
            else
                @test result.problem.A==ones(BigFloat,2,1)
                @test JSimplex._exact_rational(result.problem.objective_constant)==exact
                @test precision(result.problem.objective_constant)==ambient
                @test result.problem.objective==BigFloat[5-ratio]
                @test JSimplex.postsolve_primal(result,BigFloat[-4])==BigFloat[2,-4]
            end
            @test JSimplex._exact_rational(problem.objective_constant)==exact
            @test precision(problem.objective_constant)==256
            @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective)
        end
    end
end

@testset "Singleton constant reuse respects normal rational value semantics" begin
    T=Rational{BigInt}
    for ratio in (-3,3), initial in (T(7),T((BigInt(1)<<300)+1,BigInt(7)))
        problem=LinearProblem(sparse(T[2 1;0 1]),T[2ratio,5];objective_constant=initial,
            row_lower=[zero(T),nothing],row_upper=[zero(T),nothing],
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original=deepcopy(problem);result=JSimplex.aggregate_singleton_equalities(problem)
        @test result.problem.objective_constant==initial
        derived=result.problem.objective_constant+T(2,3)
        @test derived==original.objective_constant+T(2,3)
        result.problem.objective[1]+=1
        result.problem.A.nzval[1]+=1
        result.problem.row_upper[1]=Bound(T(20))
        @test isequal(problem.objective_constant,original.objective_constant)
        @test isequal(problem.objective,original.objective) && isequal(problem.A.nzval,original.A.nzval)
        @test isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Singleton aggregation avoids zero RHS constant arithmetic" begin
function singleton_zero_constant_shift_probe(kind; count=128, T=Float64)
    ratio=kind==:zero_ratio ? 0 : kind==:unit_positive ? 1 : kind==:unit_negative ? -1 : kind==:negative ? -3 : 3
    rhs=kind==:nonzero_rhs ? T(4) : kind in (:negative,:unit_negative) ? -zero(T) : zero(T)
    A=hcat(sparse(1:count,1:count,fill(T(2),count),count,count),sparse(ones(T,count,1)))
    problem=LinearProblem(A,[fill(T(2ratio),count);T(2)];objective_constant=T(7),
        row_lower=fill(rhs,count),row_upper=fill(rhs,count),
        column_lower=[ones(T,count);nothing],column_upper=[fill(T(3),count);nothing])
    return problem,JSimplex.aggregate_singleton_equalities
end

    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive,:negative,:unit_positive,:unit_negative,:nonzero_rhs,:zero_ratio)
        count=4;problem,pass=singleton_zero_constant_shift_probe(kind;count,T)
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
    for (kind,limit) in ((:positive,24500),(:negative,24500),(:unit_positive,24500),(:unit_negative,24500),(:nonzero_rhs,27400),(:zero_ratio,18600))
        problem,pass=singleton_zero_constant_shift_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
