using SparseArrays

@testset "Shared zero activities separate correctly after retained terms" begin
    # The four independently enumerated vertices catch accidental reuse after
    # activities diverge, or revival of a side made unbounded by an earlier term.
    cases=((3,0,0,5,0,0),(3,0,0,5,1,2),(3,1,2,-3,1,2),(3,0,2,5,1,1),
           (-3,-2,0,5,-1,1),(3,nothing,1,5,2,2),(-3,0,nothing,5,0,0),
           (3,0,0,-5,nothing,nothing))
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), pivot in (-2,-1,1,2), rhs in (0,3), (a,yl,yu,b,zl,zu) in cases, xb in ((-3,3),(nothing,2),(-2,nothing),(nothing,nothing))
        xlo,xhi=xb;cast(x)=isnothing(x) ? nothing : T(x)
        problem=LinearProblem(sparse(reshape(T[pivot,a,b],1,3)),zeros(T,3);
            row_lower=T[rhs],row_upper=T[rhs],column_lower=cast.([xlo,yl,zl]),column_upper=cast.([xhi,yu,zu]))
        original=deepcopy(problem)
        endpoints(lo,hi)=(isnothing(lo) ? -1000 : lo,isnothing(hi) ? 1000 : hi)
        vertices=[(big(rhs)//big(1)-a*y-b*z)/pivot for y in endpoints(yl,yu), z in endpoints(zl,zu)]
        expected=all(x->(isnothing(xlo) || x>=xlo) && (isnothing(xhi) || x<=xhi),vertices)
        @test JSimplex._equality_implies_column_bounds(problem,JSimplex._row_entries(problem.A)[1],1,big(pivot)//big(1),big(rhs)//big(1))==expected
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
    end
end

@testset "Sparse aggregation shares the initial zero activity" begin
function aggregation_implied_shared_zero_seed_probe(kind; count=128, T=Float64)
    pivot=kind==:negative ? T(-2) : T(2)
    term=T(3)
    low=kind==:zero_activity ? zero(T) : kind in (:variable,:lower_only,:upper_only) ? one(T) : T(2)
    high=kind==:zero_activity ? zero(T) : T(2)
    rhs=T(4)
    xlo=kind==:upper_only ? nothing : T(-8)
    xhi=kind==:lower_only ? nothing : T(8)
    rows=collect(1:2:2count);other=rows.+1
    A=sparse(vcat(rows,rows,other,other),vcat(rows,other,rows,other),
        vcat(fill(pivot,count),fill(term,count),fill(T(6),count),fill(T(5),count)),2count,2count)
    problem=LinearProblem(A,repeat(T[0,2],count);objective_constant=T(7),
        row_lower=[isodd(i) ? rhs : nothing for i in 1:2count],
        row_upper=[isodd(i) ? rhs : T(100) for i in 1:2count],
        column_lower=[isodd(i) ? xlo : low for i in 1:2count],
        column_upper=[isodd(i) ? xhi : high for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive,:negative,:zero_activity,:variable,:lower_only,:upper_only)
        count=4;problem,pass=aggregation_implied_shared_zero_seed_probe(kind;count,T)
        original=deepcopy(problem);result=pass(problem)
        term=problem.A[1,2];pivot=problem.A[1,1];rhs=bound_value(problem.row_lower[1]);y=bound_value(problem.column_lower[2])
        @test result.problem.A==spdiagm(0=>fill(T(5)-6term/pivot,count))
        @test result.problem.row_lower==fill(Bound{T}(nothing),count)
        @test result.problem.row_upper==fill(Bound(T(100)-6rhs/pivot),count)
        @test result.problem.objective==fill(T(2),count) && result.problem.objective_constant==7
        @test all(record->record.removed_row,only(result.postsolve_stack).records)
        primal=fill(y,count);restored=JSimplex.postsolve_primal(result,primal)
        @test restored==repeat(T[(rhs-term*y)/pivot,y],count)
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
    for (kind,limit) in ((:positive,42095),(:negative,42095),(:zero_activity,38767),(:variable,45679),(:lower_only,39799),(:upper_only,39415))
        problem,pass=aggregation_implied_shared_zero_seed_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
