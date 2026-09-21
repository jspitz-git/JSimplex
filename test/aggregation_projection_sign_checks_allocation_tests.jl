using SparseArrays

@testset "Projected equality bounds match independent interval images" begin
    # These small dyadic fixtures make Float64 endpoint-image enumeration exact.
    # A reversed sign must change either a projected endpoint or its infinity.
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), pivot in (-2,-1//2,1//2,2), a in (-3,3), rhs in (0,3), xb in ((-3,4),(0,0),(nothing,2),(-2,nothing),(nothing,nothing))
        lo,hi=xb;cast(x)=isnothing(x) ? nothing : T(x)
        problem=LinearProblem(sparse(T[pivot a;6 0]),T[0,2];objective_constant=T(7),
            row_lower=[T(rhs),nothing],row_upper=T[rhs,100],column_lower=[cast(lo),nothing],column_upper=[cast(hi),nothing])
        original=deepcopy(problem);result=JSimplex.aggregate_sparse_equalities(problem)
        implied=isnothing(lo)&&isnothing(hi)
        images=Float64(rhs).-Float64(pivot).*Float64[isnothing(lo) ? -Inf : lo,isnothing(hi) ? Inf : hi]
        bound(v)=isfinite(v) ? Bound(T(v)) : Bound{T}(nothing)
        lower=bound(minimum(images));upper=bound(maximum(images))
        @test result.problem.A==sparse(reshape(implied ? T[-6a/pivot] : T[a,-6a/pivot],:,1))
        @test result.problem.row_lower==(implied ? [Bound{T}(nothing)] : [lower,Bound{T}(nothing)])
        @test result.problem.row_upper==(implied ? [Bound(T(100-6rhs/pivot))] : [upper,Bound(T(100-6rhs/pivot))])
        @test result.problem.objective==T[2] && result.problem.objective_constant==7
        @test only(only(result.postsolve_stack).records).removed_row==implied
        @test JSimplex.postsolve_primal(result,T[0])==T[rhs/pivot,0]
        m=size(result.problem.A,1)
        basis=JSimplex.Basis(collect(2:m+1),[JSimplex.FREE_NONBASIC;fill(JSimplex.BASIC,m)])
        @test JSimplex.restore_basis(result,basis).basic_indices==[1,4]
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
    end
end

@testset "Projection sign checks retain BigFloat representation gates" begin
    for sign in (-1,1), exponent in (-200,0), kind in (:both,:fixed,:lower_only,:upper_only), ambient in (32,64,256)
        problem,expected_lower,expected_upper=setprecision(BigFloat,256) do
            p=sign*BigFloat(2)^exponent;value=one(BigFloat)+BigFloat(2)^(-200)
            lo=kind==:upper_only ? nothing : kind==:both ? -value : value
            hi=kind==:lower_only ? nothing : value
            problem=LinearProblem(sparse(BigFloat[p 1;p 0]),BigFloat[0,2];objective_constant=BigFloat(7),
                row_lower=[BigFloat(0),nothing],row_upper=BigFloat[0,1],column_lower=[lo,nothing],column_upper=[hi,nothing])
            images=-p.*BigFloat[isnothing(lo) ? -Inf : lo,isnothing(hi) ? Inf : hi]
            bound(v)=isfinite(v) ? Bound(v) : Bound{BigFloat}(nothing)
            problem,[bound(minimum(images)),Bound{BigFloat}(nothing)],[bound(maximum(images)),Bound(BigFloat(1))]
        end
        original=deepcopy(problem)
        setprecision(BigFloat,ambient) do
            result=JSimplex.aggregate_sparse_equalities(problem);accepted=ambient==256
            @test isempty(result.postsolve_stack)==!accepted
            @test size(result.problem.A)==(accepted ? (2,1) : (2,2))
            @test result.problem.row_lower==(accepted ? expected_lower : original.row_lower) && result.problem.row_upper==(accepted ? expected_upper : original.row_upper)
            @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
        end
    end
end

@testset "Sparse aggregation selects projection endpoints without rational sign comparisons" begin
function aggregation_projection_sign_checks_probe(kind; count=128, T=Float64)
    pivot=kind==:negative ? T(-2) : T(2)
    xlo=kind in (:upper_only,:free_pivot) ? nothing : T(-8)
    xhi=kind in (:lower_only,:free_pivot) ? nothing : T(8)
    ylo=kind in (:positive,:negative,:upper_only) ? nothing : one(T)
    yhi=kind in (:positive,:negative,:lower_only) ? nothing : T(2)
    w=one(T)
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
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive,:negative,:lower_only,:upper_only,:free_pivot,:finite)
        count=4;problem,pass=aggregation_projection_sign_checks_probe(kind;count,T)
        original=deepcopy(problem);result=pass(problem);pivot=problem.A[1,1];implied=kind in (:finite,:free_pivot)
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
    for (kind,limit) in ((:positive,72523),(:negative,72523),(:lower_only,66891),(:upper_only,66891),(:free_pivot,58643),(:finite,82835))
        problem,pass=aggregation_projection_sign_checks_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
