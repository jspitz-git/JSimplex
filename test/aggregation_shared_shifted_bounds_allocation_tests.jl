using SparseArrays

@testset "Shared shifted bounds match exact interval translation" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), pivot in (-2,-1,1,2), rhs in (-2,0,2), bounds in ((-7,-7),(0,0),(5,5),(-7,5),(nothing,5),(-7,nothing),(nothing,nothing))
        lo,hi=bounds;cast(x)=isnothing(x) ? nothing : T(x)
        problem=LinearProblem(sparse(T[pivot 3;6 5]),T[0,2];objective_constant=T(7),
            row_lower=[T(rhs),cast(lo)],row_upper=[T(rhs),cast(hi)],column_lower=[nothing,nothing],column_upper=[nothing,nothing])
        original=deepcopy(problem);result=JSimplex.aggregate_sparse_equalities(problem)
        shift=big(6)*rhs//big(pivot)
        translated(x)=isnothing(x) ? Bound{T}(nothing) : Bound(T(x-shift))
        @test result.problem.A==reshape(T[5-18/pivot],1,1)
        @test result.problem.row_lower==[translated(lo)]
        @test result.problem.row_upper==[translated(hi)]
        @test result.problem.objective==T[2] && result.problem.objective_constant==7
        @test only(only(result.postsolve_stack).records).removed_row
        @test JSimplex.postsolve_primal(result,T[0])==T[rhs/pivot,0]
        basis=JSimplex.Basis([2],[JSimplex.FREE_NONBASIC,JSimplex.BASIC])
        @test JSimplex.restore_basis(result,basis).basic_indices==[1,4]
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Zero shifts retain distinct bound representations" begin
    for T in (Float32,Float64)
        problem=LinearProblem(sparse(T[2 3;6 5]),T[0,2];row_lower=T[0,-0.0],row_upper=T[0,0.0],
            column_lower=[nothing,nothing],column_upper=[nothing,nothing])
        original=deepcopy(problem);result=JSimplex.aggregate_sparse_equalities(problem)
        @test isequal(bound_value(only(result.problem.row_lower)),T(-0.0))
        @test isequal(bound_value(only(result.problem.row_upper)),T(0.0))
        @test isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
    problem=setprecision(BigFloat,256) do
        LinearProblem(sparse(BigFloat[2 3;6 5]),BigFloat[0,2];row_lower=BigFloat[0,20],row_upper=BigFloat[0,20],
            column_lower=[nothing,nothing],column_upper=[nothing,nothing])
    end
    problem.row_lower[2]=Bound(setprecision(()->BigFloat(20),BigFloat,128))
    for ambient in (32,64,256)
        setprecision(BigFloat,ambient) do
            result=JSimplex.aggregate_sparse_equalities(problem)
            @test precision(bound_value(only(result.problem.row_lower)))==128
            @test precision(bound_value(only(result.problem.row_upper)))==256
            @test precision(bound_value(problem.row_lower[2]))==128 && precision(bound_value(problem.row_upper[2]))==256
        end
    end
end

@testset "Shared shifted bounds preserve BigFloat gates and unequal neighbors" begin
    for pivot in (-2,2), kind in (:equal_inexact,:unequal_neighbor,:equal_exact), ambient in (32,64,256)
        problem,expected_lower,expected_upper=setprecision(BigFloat,256) do
            tiny=BigFloat(2)^(-200)
            low=kind==:equal_inexact ? one(BigFloat)+tiny : BigFloat(20)
            high=kind==:unequal_neighbor ? low+tiny : low
            p=LinearProblem(sparse(BigFloat[pivot 3;6 0]),BigFloat[0,2];objective_constant=BigFloat(7),
                row_lower=BigFloat[4,low],row_upper=BigFloat[4,high],column_lower=[nothing,nothing],column_upper=[nothing,nothing])
            p,low-24/pivot,high-24/pivot
        end
        original=deepcopy(problem)
        setprecision(BigFloat,ambient) do
            result=JSimplex.aggregate_sparse_equalities(problem);accepted=ambient==256 || kind==:equal_exact
            @test isempty(result.postsolve_stack)==!accepted
            @test size(result.problem.A)==(accepted ? (1,1) : (2,2))
            @test result.problem.row_lower==(accepted ? [Bound(expected_lower)] : original.row_lower) && result.problem.row_upper==(accepted ? [Bound(expected_upper)] : original.row_upper)
            @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
        end
    end
    for T in (Float32,Float64)
        problem=LinearProblem(sparse(T[1 3;2 0]),T[0,2];row_lower=T[-floatmax(T),floatmax(T)],row_upper=T[-floatmax(T),floatmax(T)],
            column_lower=[nothing,nothing],column_upper=[nothing,nothing])
        original=deepcopy(problem);result=JSimplex.aggregate_sparse_equalities(problem)
        @test result.problem===problem
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Shared bound shifts accumulate in private equality bounds" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), free in (false,true)
        problem=LinearProblem(sparse(T[1 0 1 0 0;0 1 0 1 0;2 3 0 0 1]),T[2,3,4,5,6];
            row_lower=T[4,6,30],row_upper=T[4,6,30],column_lower=free ? fill(nothing,5) : [T(0),T(0),nothing,nothing,nothing],
            column_upper=free ? fill(nothing,5) : [T(1),T(1),nothing,nothing,nothing])
        original=deepcopy(problem);result=JSimplex.aggregate_sparse_equalities(problem)
        @test result.problem.A==(free ? reshape(T[-2,-3,1],1,3) : T[1 0 0;0 1 0;-2 -3 1])
        @test bound_value.(result.problem.row_lower)==(free ? T[4] : T[3,5,4])
        @test bound_value.(result.problem.row_upper)==(free ? T[4] : T[4,6,4])
        @test result.problem.objective==T[2,2,6] && result.problem.objective_constant==26
        @test length(only(result.postsolve_stack).records)==2
        @test JSimplex.postsolve_primal(result,T[3,5,25])==T[1,1,3,5,25]
        m,n=size(result.problem.A);basis=JSimplex.Basis(collect(n+1:n+m),[fill(JSimplex.FREE_NONBASIC,n);fill(JSimplex.BASIC,m)])
        @test JSimplex.restore_basis(result,basis).basic_indices==[1,2,8]
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Sparse aggregation shares nonzero shifts of equal bounds" begin
function aggregation_shared_shifted_bounds_probe(kind; count=128, T=Float64)
    pivot=kind==:negative ? T(-2) : T(2)
    rhs=kind==:zero_shift ? zero(T) : T(4)
    upper=kind==:negative ? T(16) : kind==:cancelled ? T(12) : kind==:zero_bound ? zero(T) : T(20)
    lower=kind==:unequal ? T(-20) : upper
    rows=collect(1:2:2count);other=rows.+1
    A=sparse(vcat(rows,rows,other,other),vcat(rows,other,rows,other),
        vcat(fill(pivot,count),fill(T(3),count),fill(T(6),count),fill(T(5),count)),2count,2count)
    problem=LinearProblem(A,repeat(T[0,2],count);objective_constant=T(7),
        row_lower=[isodd(i) ? rhs : lower for i in 1:2count],
        row_upper=[isodd(i) ? rhs : upper for i in 1:2count],
        column_lower=fill(nothing,2count),column_upper=fill(nothing,2count))
    return problem,JSimplex.aggregate_sparse_equalities
end
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive,:negative,:cancelled,:zero_bound,:unequal,:zero_shift)
        count=4;problem,pass=aggregation_shared_shifted_bounds_probe(kind;count,T)
        original=deepcopy(problem);result=pass(problem);pivot=problem.A[1,1];rhs=bound_value(problem.row_lower[1]);shift=6rhs/pivot
        @test result.problem.A==spdiagm(0=>fill(T(5)-18/pivot,count))
        @test result.problem.row_lower==fill(Bound(bound_value(problem.row_lower[2])-shift),count)
        @test result.problem.row_upper==fill(Bound(bound_value(problem.row_upper[2])-shift),count)
        @test result.problem.objective==fill(T(2),count) && result.problem.objective_constant==7
        @test all(record->record.removed_row,only(result.postsolve_stack).records)
        y=kind==:unequal ? zero(T) : (bound_value(problem.row_upper[2])-shift)/(5-18/pivot)
        primal=fill(y,count);restored=JSimplex.postsolve_primal(result,primal)
        @test restored==repeat(T[(rhs-3y)/pivot,y],count)
        @test problem.objective_constant+sum(problem.objective.*restored)==result.problem.objective_constant+sum(result.problem.objective.*primal)
        m,n=size(result.problem.A)
        for state in (JSimplex.AT_LOWER,JSimplex.AT_UPPER)
            basis=JSimplex.Basis(collect(n+1:n+m),[fill(state,n);fill(JSimplex.BASIC,m)])
            restored_basis=JSimplex.restore_basis(result,basis)
            @test restored_basis.basic_indices==[isodd(i) ? i : 2count+i for i in 1:2count]
            @test restored_basis.states[2:2:2count]==fill(state,count)
        end
        result.problem.objective[1]+=one(T);result.problem.A.nzval[1]+=one(T)
        result.problem.row_upper[1]=Bound(T(20))
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective)
        @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
        @test isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
    for (kind,limit) in ((:positive,33831),(:negative,33831),(:cancelled,31783),(:zero_bound,28967),(:unequal,34295),(:zero_shift,23543))
        problem,pass=aggregation_shared_shifted_bounds_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
