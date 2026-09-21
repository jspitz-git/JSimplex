using SparseArrays

@testset "Doubleton shared shifted bounds match exact interval translation" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), pivot in (-2,-1,1,2), rhs in (-2,0,2), bounds in ((-7,-7),(0,0),(5,5),(-7,5),(nothing,5),(-7,nothing),(nothing,nothing))
        lo,hi=bounds;cast(x)=isnothing(x) ? nothing : T(x)
        problem=LinearProblem(sparse(T[pivot 3;6 5]),T[0,2];objective_constant=T(7),
            row_lower=[T(rhs),cast(lo)],row_upper=[T(rhs),cast(hi)],column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
        original=deepcopy(problem);result=JSimplex.substitute_free_doubleton(problem)
        shift=big(6)*rhs//big(pivot)
        translated(x)=isnothing(x) ? Bound{T}(nothing) : Bound(T(x-shift))
        @test result.problem.A==reshape(T[5-18/pivot],1,1)
        @test result.problem.row_lower==[translated(lo)]
        @test result.problem.row_upper==[translated(hi)]
        @test result.problem.objective==T[2] && result.problem.objective_constant==7
        @test only(result.postsolve_stack).eliminated==1 && only(result.postsolve_stack).equality_row==1
        @test JSimplex.postsolve_primal(result,T[0])==T[rhs/pivot,0]
        basis=JSimplex.Basis([2],[JSimplex.FREE_NONBASIC,JSimplex.BASIC])
        @test JSimplex.restore_basis(result,basis).basic_indices==[1,4]
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Doubleton zero shifts retain distinct bound representations" begin
    for T in (Float32,Float64)
        problem=LinearProblem(sparse(T[2 3;6 5]),T[0,2];row_lower=T[0,-0.0],row_upper=T[0,0.0],
            column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
        original=deepcopy(problem);result=JSimplex.substitute_free_doubleton(problem)
        @test isequal(bound_value(only(result.problem.row_lower)),T(-0.0))
        @test isequal(bound_value(only(result.problem.row_upper)),T(0.0))
        @test isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
    problem=setprecision(BigFloat,256) do
        LinearProblem(sparse(BigFloat[2 3;6 5]),BigFloat[0,2];row_lower=BigFloat[0,20],row_upper=BigFloat[0,20],
            column_lower=[nothing,BigFloat(-10)],column_upper=[nothing,BigFloat(10)])
    end
    problem.row_lower[2]=Bound(setprecision(()->BigFloat(20),BigFloat,128))
    for ambient in (32,64,256)
        setprecision(BigFloat,ambient) do
            result=JSimplex.substitute_free_doubleton(problem)
            @test precision(bound_value(only(result.problem.row_lower)))==128
            @test precision(bound_value(only(result.problem.row_upper)))==256
            @test precision(bound_value(problem.row_lower[2]))==128 && precision(bound_value(problem.row_upper[2]))==256
        end
    end
end

@testset "Doubleton shared shifts preserve BigFloat gates and unequal neighbors" begin
    for pivot in (-2,2), kind in (:equal_inexact,:unequal_neighbor,:equal_exact), ambient in (32,64,256)
        problem,expected_lower,expected_upper=setprecision(BigFloat,256) do
            tiny=BigFloat(2)^(-200)
            low=kind==:equal_inexact ? one(BigFloat)+tiny : BigFloat(20)
            high=kind==:unequal_neighbor ? low+tiny : low
            p=LinearProblem(sparse(BigFloat[pivot 3;6 0]),BigFloat[0,2];objective_constant=BigFloat(7),
                row_lower=BigFloat[4,low],row_upper=BigFloat[4,high],column_lower=[nothing,BigFloat(-10)],column_upper=[nothing,BigFloat(10)])
            p,low-24/pivot,high-24/pivot
        end
        original=deepcopy(problem)
        setprecision(BigFloat,ambient) do
            result=JSimplex.substitute_free_doubleton(problem);accepted=ambient==256 || kind==:equal_exact
            @test isempty(result.postsolve_stack)==!accepted
            @test size(result.problem.A)==(accepted ? (1,1) : (2,2))
            @test result.problem.row_lower==(accepted ? [Bound(expected_lower)] : original.row_lower) && result.problem.row_upper==(accepted ? [Bound(expected_upper)] : original.row_upper)
            @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
        end
    end
    for T in (Float32,Float64)
        problem=LinearProblem(sparse(T[1 3;2 0]),T[0,2];row_lower=T[-floatmax(T),floatmax(T)],row_upper=T[-floatmax(T),floatmax(T)],
            column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
        original=deepcopy(problem);result=JSimplex.substitute_free_doubleton(problem)
        @test result.problem===problem
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Rejected doubleton shared shifts do not leak into a later substitution" begin
    for T in (Float32,Float64), lower in (0,1)
        problem=LinearProblem(sparse(T[1 1 0 0;2 1 0 1;0.1 0 0 1;0 0 1 1]),T[0,2,0,3];objective_constant=T(7),
            row_lower=T[0.5,20,lower,2],row_upper=T[0.5,20,2,2],
            column_lower=[nothing,T(-10),nothing,T(-10)],column_upper=[nothing,T(10),nothing,T(10)])
        original=deepcopy(problem);result=JSimplex.substitute_free_doubleton(problem)
        @test only(result.postsolve_stack).eliminated==3 && only(result.postsolve_stack).equality_row==4
        @test result.problem.A==problem.A[1:3,[1,2,4]]
        @test result.problem.row_lower==problem.row_lower[1:3] && result.problem.row_upper==problem.row_upper[1:3]
        @test result.problem.objective==T[0,2,3] && result.problem.objective_constant==7
        @test JSimplex.postsolve_primal(result,T[0.5,0,0])==T[0.5,0,2,0]
        basis=JSimplex.Basis([4,5,6],[fill(JSimplex.FREE_NONBASIC,3);fill(JSimplex.BASIC,3)])
        @test JSimplex.restore_basis(result,basis).basic_indices==[5,6,7,3]
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Doubleton substitution shares nonzero shifts of equal bounds" begin
function doubleton_shared_shifted_bounds_probe(kind; count=128, T=Float64)
    pivot=kind==:negative ? T(-2) : T(2)
    rhs=kind==:zero_shift ? zero(T) : T(4)
    upper=kind==:negative ? T(16) : kind==:cancelled ? T(12) : kind==:zero_bound ? zero(T) : T(20)
    lower=kind==:unequal ? T(-20) : upper
    A=sparse(hcat(vcat(pivot,fill(T(6),count)),vcat(T(3),fill(T(5),count))))
    problem=LinearProblem(A,T[0,2];objective_constant=T(7),
        row_lower=vcat(rhs,fill(lower,count)),row_upper=vcat(rhs,fill(upper,count)),
        column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
    return problem,JSimplex.substitute_free_doubleton
end
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive,:negative,:cancelled,:zero_bound,:unequal,:zero_shift)
        count=4;problem,pass=doubleton_shared_shifted_bounds_probe(kind;count,T)
        original=deepcopy(problem);result=pass(problem);pivot=problem.A[1,1];rhs=bound_value(problem.row_lower[1]);shift=6rhs/pivot
        @test result.problem.A==fill(T(5)-18/pivot,count,1)
        @test result.problem.row_lower==fill(Bound(bound_value(problem.row_lower[2])-shift),count)
        @test result.problem.row_upper==fill(Bound(bound_value(problem.row_upper[2])-shift),count)
        @test result.problem.objective==T[2] && result.problem.objective_constant==7
        @test only(result.postsolve_stack).eliminated==1 && only(result.postsolve_stack).equality_row==1
        primal=T[1];restored=JSimplex.postsolve_primal(result,primal)
        @test restored==T[(rhs-3)/pivot,1]
        @test problem.objective_constant+sum(problem.objective.*restored)==result.problem.objective_constant+sum(result.problem.objective.*primal)
        for state in (JSimplex.AT_LOWER,JSimplex.AT_UPPER)
            basis=JSimplex.Basis(collect(2:count+1),[state;fill(JSimplex.BASIC,count)]);restored_basis=JSimplex.restore_basis(result,basis)
            @test restored_basis.basic_indices==[1;collect(4:count+3)]
            @test restored_basis.states[1:2]==[JSimplex.BASIC,state]
        end
        result.problem.objective[1]+=one(T);result.problem.A.nzval[1]+=one(T);result.problem.row_upper[1]=Bound(T(20))
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective)
        @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
        @test isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
    for (kind,limit) in ((:positive,16114),(:negative,16114),(:cancelled,14578),(:zero_bound,11762),(:unequal,17178),(:zero_shift,7307))
        problem,pass=doubleton_shared_shifted_bounds_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
