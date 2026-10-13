using SparseArrays

@testset "Implied bounds preserve zero and cancelling activities" begin
    # Endpoint enumeration detects a swapped minimum/maximum, a lost nonzero
    # activity, or a skipped division by the signed pivot.
    cases=((3,0,0,1,0),(3,0,2,1,0),(3,-2,0,1,0),
           (3,1,1,-3,1),(-3,1,1,3,1),(3,1,2,-3,1),
           (3,0,1,-3,1),(1,nothing,0,3,0),(-1,0,nothing,3,0),
           (3,1//2,1,1,0))
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), pivot in (-2,2), rhs in (-4,0,4), (a,lo,hi,b,z) in cases, xb in ((-3,3),(0,0),(nothing,2),(-2,nothing),(nothing,nothing))
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

@testset "Zero activity preserves stored RHS precision and tiny residuals" begin
    for source in (:rhs,:activity), near in (false,true), direction in (-1,1), ambient in (32,64,256), cancellation in (false,true)
        problem=setprecision(BigFloat,256) do
            delta=near ? direction*BigFloat(2)^(-200) : zero(BigFloat)
            rhs=source==:rhs ? BigFloat(4)+delta : BigFloat(4)
            value=source==:activity ? delta : zero(BigFloat)
            terms=cancellation ? BigFloat[2,1,3,-3] : BigFloat[2,1]
            bounds=cancellation ? BigFloat[value,1,1] : BigFloat[value]
            # A positive RHS residual violates x<=2; a positive activity
            # residual violates x>=2. The reverse applies to negative residuals.
            upper=(source==:rhs)==(direction>0)
            LinearProblem(sparse(reshape(terms,1,:)),zeros(BigFloat,length(terms));
                row_lower=[rhs],row_upper=[rhs],
                column_lower=[upper ? nothing : BigFloat(2);bounds],
                column_upper=[upper ? BigFloat(2) : nothing;bounds])
        end
        original=deepcopy(problem);rhs=JSimplex._exact_rational(bound_value(problem.row_lower[1]))
        setprecision(BigFloat,ambient) do
            @test JSimplex._equality_implies_column_bounds(problem,JSimplex._row_entries(problem.A)[1],1,big(2)//big(1),rhs)==!near
            @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower)
            @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
        end
    end
end

@testset "Zero activity preserves large rational RHS thresholds" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), pivot in (-2,2), direction in (-1,1), offset in (0,1)
        rhs=T(direction*((BigInt(1)<<300)+1),BigInt(den));x=rhs/pivot
        problem=LinearProblem(sparse(reshape(T[pivot,3,-3],1,3)),zeros(T,3);
            row_lower=T[rhs],row_upper=T[rhs],column_lower=T[x+offset,1,1],column_upper=T[x+offset,1,1])
        @test JSimplex._equality_implies_column_bounds(problem,JSimplex._row_entries(problem.A)[1],1,T(pivot),rhs)==(offset==0)
    end
end

@testset "Sparse aggregation skips subtracting zero activity" begin
function aggregation_implied_zero_activity_probe(kind; count=128, T=Float64)
    pivot=kind==:negative_pivot ? T(-2) : T(2)
    low=kind==:upper_zero ? T(-2) : kind==:nonzero ? T(1)/2 : zero(T)
    high=kind==:lower_zero ? T(2) : kind==:nonzero ? one(T) : zero(T)
    xlo=kind==:free_pivot ? nothing : pivot<0 ? T(-3) : one(T)
    xhi=kind==:free_pivot ? nothing : pivot<0 ? T(-1) : T(3)
    odd=collect(1:2:2count);even=odd.+1
    A=sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(pivot,count),fill(T(3),count),fill(T(6),count),fill(T(5),count)),2count,2count)
    problem=LinearProblem(A,[isodd(i) ? zero(T) : T(2) for i in 1:2count];objective_constant=T(7),
        row_lower=[isodd(i) ? T(4) : nothing for i in 1:2count],
        row_upper=[isodd(i) ? T(4) : T(100) for i in 1:2count],
        column_lower=[isodd(i) ? xlo : low for i in 1:2count],
        column_upper=[isodd(i) ? xhi : high for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive_pivot,:negative_pivot,:lower_zero,:upper_zero,:nonzero,:free_pivot)
        count=4;problem,pass=aggregation_implied_zero_activity_probe(kind;count,T)
        original=deepcopy(problem);result=pass(problem)
        implied=kind in (:positive_pivot,:negative_pivot,:free_pivot)
        term=problem.A[1,2];pivot=problem.A[1,1];multiplier=6/pivot;upper=100-4multiplier
        expected=implied ? spdiagm(0=>fill(T(5)-multiplier*term,count)) :
            sparse(collect(1:2count),repeat(collect(1:count),inner=2),repeat(T[term,5-multiplier*term],count),2count,count)
        @test result.problem.A==expected
        @test result.problem.row_lower==(implied ? fill(Bound{T}(nothing),count) : [isodd(i) ? Bound(T(-2)) : Bound{T}(nothing) for i in 1:2count])
        @test result.problem.row_upper==(implied ? fill(Bound(T(upper)),count) : [Bound(isodd(i) ? T(2) : T(upper)) for i in 1:2count])
        @test result.problem.objective==fill(T(2),count) && result.problem.objective_constant==7
        @test all(record->record.removed_row==implied,only(result.postsolve_stack).records)
        y=kind==:nonzero ? T(1)/2 : zero(T);primal=fill(y,count)
        restored=JSimplex.postsolve_primal(result,primal)
        @test restored==repeat(T[(4-term*y)/pivot,y],count)
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
    for (kind,limit) in ((:positive_pivot,42173),(:negative_pivot,42173),(:lower_zero,55755),(:upper_zero,55755),(:nonzero,59327),(:free_pivot,29873))
        problem,pass=aggregation_implied_zero_activity_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
