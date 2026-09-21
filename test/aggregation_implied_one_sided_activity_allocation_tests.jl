using SparseArrays

@testset "One-sided implied activities match endpoint enumeration" begin
    # Endpoint enumeration detects a swapped minimum/maximum, a lost nonzero
    # activity, or a skipped division by the signed pivot.
    cases=((3,1,1,5,1),(-3,1,1,-5,1),(1//2,1,1,3//2,1),
           (-1//2,1,1,-3//2,1),(3,1,1,-3,1),(3,1,2,-3,1),
           (1//2,1,1,1//4,1),(1,nothing,1,3,1),(-1,-1,nothing,3,1),(3,0,0,1,0))
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), pivot in (-2,2), rhs in (-3,0,3), (a,lo,hi,b,z) in cases, xb in ((-3,3),(0,0),(nothing,2),(-2,nothing),(nothing,nothing))
        xlo,xhi=xb;cast(x)=isnothing(x) ? nothing : T(x)
        problem=LinearProblem(sparse(reshape(T[pivot,a,b],1,3)),zeros(T,3);
            row_lower=T[rhs],row_upper=T[rhs],column_lower=cast.([xlo,lo,z]),column_upper=cast.([xhi,hi,z]))
        original=deepcopy(problem)
        # These witnesses exceed every finite pivot bound for these small coefficients.
        endpoints=(isnothing(lo) ? -1000 : lo,isnothing(hi) ? 1000 : hi)
        vertices=[(big(rhs)//big(1)-a*y-b*z)/pivot for y in endpoints]
        expected=all(x->(isnothing(xlo) || x>=xlo) && (isnothing(xhi) || x<=xhi),vertices)
        @test JSimplex._equality_implies_column_bounds(problem,JSimplex._row_entries(problem.A)[1],1,big(pivot)//big(1),big(rhs)//big(1))==expected
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
    end
end

@testset "One-sided implied activities compare stored BigFloat endpoint precision" begin
    for pivot in (-2,-1,1,2), side in (:lower,:upper), offset in (0,1,2), ambient in (32,64,256)
        problem=setprecision(BigFloat,256) do
            tiny=BigFloat(2)^(-200);value=BigFloat(2)+tiny;candidate=BigFloat(1)+tiny
            rhs=3value+pivot*candidate
            low=side==:lower ? BigFloat(1)+offset*tiny : nothing
            high=side==:upper ? BigFloat(1)+offset*tiny : nothing
            LinearProblem(sparse(reshape(BigFloat[pivot,3],1,2)),zeros(BigFloat,2);
                row_lower=[rhs],row_upper=[rhs],column_lower=[low,value],column_upper=[high,value])
        end
        original=deepcopy(problem);rhs=JSimplex._exact_rational(bound_value(problem.row_lower[1]))
        expected=side==:lower ? offset<=1 : offset>=1
        setprecision(BigFloat,ambient) do
            @test JSimplex._equality_implies_column_bounds(problem,JSimplex._row_entries(problem.A)[1],1,big(pivot)//big(1),rhs)==expected
            @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower)
            @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
        end
    end
end

@testset "One-sided implied activities preserve large rational bound decisions" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), pivot in (-2,-1,1,2), side in (:lower,:upper), offset in (0,1)
        candidate=T((BigInt(1)<<300)+1,BigInt(den));rhs=T(6)+pivot*candidate
        delta=T(1,BigInt(1)<<350)
        low=side==:lower ? candidate+offset*delta : nothing
        high=side==:upper ? candidate-offset*delta : nothing
        problem=LinearProblem(sparse(reshape(T[pivot,3],1,2)),zeros(T,2);
            row_lower=T[rhs],row_upper=T[rhs],column_lower=[low,T(2)],column_upper=[high,T(2)])
        original=deepcopy(problem)
        @test JSimplex._equality_implies_column_bounds(problem,JSimplex._row_entries(problem.A)[1],1,T(pivot),rhs)==(offset==0)
        @test problem.column_lower==original.column_lower && problem.column_upper==original.column_upper
    end
end

@testset "Sparse aggregation skips unused implied activity" begin
function aggregation_implied_one_sided_activity_probe(kind; count=128, T=Float64)
    pivot=kind in (:lower_negative,:upper_negative) ? T(-2) : T(2)
    term=T(3);low=one(T);high=T(2)
    xlo=kind in (:upper_positive,:upper_negative,:free_pivot) ? nothing : T(-8)
    xhi=kind in (:lower_positive,:lower_negative,:free_pivot) ? nothing : T(8)
    rows=collect(1:2:2count);other=rows.+1
    A=sparse(vcat(rows,rows,other,other),vcat(rows,other,rows,other),
        vcat(fill(pivot,count),fill(term,count),fill(T(6),count),fill(T(5),count)),2count,2count)
    problem=LinearProblem(A,repeat(T[0,2],count);objective_constant=T(7),
        row_lower=[isodd(i) ? T(4) : nothing for i in 1:2count],
        row_upper=[isodd(i) ? T(4) : T(100) for i in 1:2count],
        column_lower=[isodd(i) ? xlo : low for i in 1:2count],
        column_upper=[isodd(i) ? xhi : high for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:lower_positive,:lower_negative,:upper_positive,:upper_negative,:both,:free_pivot)
        count=4;problem,pass=aggregation_implied_one_sided_activity_probe(kind;count,T)
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
    for (kind,limit) in ((:lower_positive,41639),(:lower_negative,42407),(:upper_positive,42407),(:upper_negative,41639),(:both,45943),(:free_pivot,29687))
        problem,pass=aggregation_implied_one_sided_activity_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
