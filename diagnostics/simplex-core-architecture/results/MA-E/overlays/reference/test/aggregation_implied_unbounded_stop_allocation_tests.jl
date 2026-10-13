using SparseArrays

@testset "Unbounded activity stopping matches endpoint enumeration" begin
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

@testset "Sparse aggregation projects bounds after unbounded activity" begin
function aggregation_implied_unbounded_stop_probe(kind; count=128, T=Float64)
    pivot=kind==:negative ? T(-2) : T(2)
    xlo=kind==:upper_only ? nothing : T(-8)
    xhi=kind==:lower_only ? nothing : T(8)
    ylo=kind in (:positive,:negative,:upper_only) ? nothing : one(T)
    yhi=kind in (:positive,:negative,:lower_only) ? nothing : T(2)
    w=kind==:late_unbounded ? nothing : one(T)
    rows=collect(1:2:2count);other=rows.+1;cols=collect(1:4:4count)
    A=sparse(vcat(rows,rows,rows,rows,other,other,other,other),
        vcat(cols,cols.+1,cols.+2,cols.+3,cols,cols.+1,cols.+2,cols.+3),
        vcat(fill(pivot,count),fill(T(3),count),fill(T(5),count),fill(T(7),count),
             fill(T(6),count),fill(T(5),count),fill(T(7),count),fill(T(9),count)),2count,4count)
    problem=LinearProblem(A,repeat(T[0,2,3,4],count);objective_constant=T(7),
        row_lower=[isodd(i) ? T(4) : nothing for i in 1:2count],
        row_upper=[isodd(i) ? T(4) : T(100) for i in 1:2count],
        column_lower=repeat([xlo,ylo,one(T),w],count),
        column_upper=repeat([xhi,yhi,one(T),w],count))
    return problem,JSimplex.aggregate_sparse_equalities
end
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive,:negative,:lower_only,:upper_only,:late_unbounded,:finite)
        count=4;problem,pass=aggregation_implied_unbounded_stop_probe(kind;count,T)
        original=deepcopy(problem);result=pass(problem);pivot=problem.A[1,1];implied=kind==:finite
        m=implied ? count : 2count;n=3count;expected=zeros(T,m,n)
        for block in 1:count
            row=implied ? block : 2block-1;column=3block-2
            if !implied
                expected[row,column:column+2].=T[3,5,7]
                row+=1
            end
            expected[row,column:column+2].=T[5-18/pivot,7-30/pivot,9-42/pivot]
        end
        projected_lower=kind==:lower_only ? nothing : T(-12)
        projected_upper=kind==:upper_only ? nothing : T(20)
        @test result.problem.A==sparse(expected)
        @test result.problem.row_lower==(implied ? fill(Bound{T}(nothing),count) : repeat([Bound{T}(projected_lower),Bound{T}(nothing)],count))
        @test result.problem.row_upper==(implied ? fill(Bound(T(100)-24/pivot),count) : repeat([Bound{T}(projected_upper),Bound(T(100)-24/pivot)],count))
        @test result.problem.objective==repeat(T[2,3,4],count) && result.problem.objective_constant==7
        retained=[i for i in 1:4count if mod1(i,4)!=1]
        @test result.problem.column_lower==problem.column_lower[retained] && result.problem.column_upper==problem.column_upper[retained]
        @test all(record->record.removed_row==implied,only(result.postsolve_stack).records)
        primal=ones(T,n);restored=JSimplex.postsolve_primal(result,primal)
        @test restored==repeat(T[-11/pivot,1,1,1],count)
        @test problem.objective_constant+sum(problem.objective.*restored)==result.problem.objective_constant+sum(result.problem.objective.*primal)
        for state in (JSimplex.AT_LOWER,JSimplex.AT_UPPER)
            basis=JSimplex.Basis(collect(n+1:n+m),[fill(state,n);fill(JSimplex.BASIC,m)])
            restored_basis=JSimplex.restore_basis(result,basis)
            @test restored_basis.basic_indices==[isodd(i) ? 4*((i-1)÷2)+1 : 4count+i for i in 1:2count]
            @test restored_basis.states[retained]==fill(state,n)
        end
        result.problem.objective[1]+=one(T);result.problem.A.nzval[1]+=one(T)
        result.problem.row_upper[1]=Bound(T(20))
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective)
        @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
        @test isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
    for (kind,limit) in ((:positive,75595),(:negative,75595),(:lower_only,69963),(:upper_only,69963),(:late_unbounded,84251),(:finite,82835))
        problem,pass=aggregation_implied_unbounded_stop_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
