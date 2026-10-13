using SparseArrays

@testset "Signed-unit pivots preserve endpoint-derived bounds" begin
    # Endpoint enumeration detects a swapped minimum/maximum, a lost nonzero
    # activity, or a skipped division by the signed pivot.
    cases=((3,0,0,1,0),(3,0,2,1,0),(3,-2,0,1,0),
           (3,1,1,-3,1),(-3,1,1,3,1),(3,1,2,-3,1),
           (3,0,1,-3,1),(1,nothing,0,3,0),(-1,0,nothing,3,0),
           (3,1//2,1,1,0))
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), pivot in (-1,1), rhs in (-4,0,4), (a,lo,hi,b,z) in cases, xb in ((-3,3),(0,0),(nothing,2),(-2,nothing),(nothing,nothing))
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

@testset "Unit division preserves stored RHS precision and tiny residuals" begin
    for source in (:rhs,:activity), near in (false,true), direction in (-1,1), ambient in (32,64,256), cancellation in (false,true)
        problem=setprecision(BigFloat,256) do
            delta=near ? direction*BigFloat(2)^(-200) : zero(BigFloat)
            rhs=source==:rhs ? BigFloat(4)+delta : BigFloat(4)
            value=source==:activity ? delta : zero(BigFloat)
            terms=cancellation ? BigFloat[1,1,3,-3] : BigFloat[1,1]
            bounds=cancellation ? BigFloat[value,1,1] : BigFloat[value]
            # A positive RHS residual violates x<=4; a positive activity
            # residual violates x>=4. The reverse applies to negative residuals.
            upper=(source==:rhs)==(direction>0)
            LinearProblem(sparse(reshape(terms,1,:)),zeros(BigFloat,length(terms));
                row_lower=[rhs],row_upper=[rhs],
                column_lower=[upper ? nothing : BigFloat(4);bounds],
                column_upper=[upper ? BigFloat(4) : nothing;bounds])
        end
        original=deepcopy(problem);rhs=JSimplex._exact_rational(bound_value(problem.row_lower[1]))
        setprecision(BigFloat,ambient) do
            @test JSimplex._equality_implies_column_bounds(problem,JSimplex._row_entries(problem.A)[1],1,big(1)//big(1),rhs)==!near
            @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower)
            @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
        end
    end
end

@testset "Signed-unit division preserves large rational thresholds" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), pivot in (-1,1), direction in (-1,1), offset in (0,1)
        rhs=T(direction*((BigInt(1)<<300)+1),BigInt(den));x=rhs/pivot
        problem=LinearProblem(sparse(reshape(T[pivot,3,-3],1,3)),zeros(T,3);
            row_lower=T[rhs],row_upper=T[rhs],column_lower=T[x+offset,1,1],column_upper=T[x+offset,1,1])
        @test JSimplex._equality_implies_column_bounds(problem,JSimplex._row_entries(problem.A)[1],1,T(pivot),rhs)==(offset==0)
    end
end

@testset "Implied division distinguishes signed-unit pivot neighbors" begin
    for direction in (-1,1), near in (false,true), ambient in (32,64,256), cancellation in (false,true)
        problem=setprecision(BigFloat,256) do
            pivot=direction*(BigFloat(1)+(near ? BigFloat(2)^(-200) : zero(BigFloat)))
            terms=cancellation ? BigFloat[pivot,3,-3] : BigFloat[pivot,3]
            bounds=cancellation ? BigFloat[1,1] : BigFloat[0]
            LinearProblem(sparse(reshape(terms,1,:)),zeros(BigFloat,length(terms));
                row_lower=BigFloat[4direction],row_upper=BigFloat[4direction],
                column_lower=[BigFloat(4);bounds],column_upper=[nothing;bounds])
        end
        original=deepcopy(problem)
        pivot=JSimplex._exact_rational(problem.A[1,1]);rhs=big(4direction)//big(1)
        setprecision(BigFloat,ambient) do
            @test JSimplex._equality_implies_column_bounds(problem,JSimplex._row_entries(problem.A)[1],1,pivot,rhs)==!near
            @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
        end
    end
end

@testset "Sparse aggregation skips division by signed-unit pivots" begin
function aggregation_implied_unit_division_probe(kind; count=128, T=Float64)
    pivot=kind in (:negative,:fixed_negative) ? -one(T) : kind==:nonunit ? T(2) : one(T)
    fixed=kind in (:fixed_positive,:fixed_negative)
    low=zero(T);high=fixed ? zero(T) : T(2)
    xlo=kind==:free_pivot ? nothing : pivot<0 ? (fixed ? T(-5) : T(-3)) : (fixed ? T(3) : one(T))
    xhi=kind==:free_pivot ? nothing : pivot<0 ? (fixed ? T(-3) : T(-1)) : (fixed ? T(5) : T(3))
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
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive,:negative,:fixed_positive,:fixed_negative,:nonunit,:free_pivot)
        count=4;problem,pass=aggregation_implied_unit_division_probe(kind;count,T)
        original=deepcopy(problem);result=pass(problem)
        implied=kind in (:fixed_positive,:fixed_negative,:free_pivot)
        term=problem.A[1,2];pivot=problem.A[1,1];multiplier=6/pivot;upper=100-4multiplier
        expected=implied ? spdiagm(0=>fill(T(5)-multiplier*term,count)) :
            sparse(collect(1:2count),repeat(collect(1:count),inner=2),repeat(T[term,5-multiplier*term],count),2count,count)
        @test result.problem.A==expected
        @test result.problem.row_lower==(implied ? fill(Bound{T}(nothing),count) : [isodd(i) ? Bound(kind==:nonunit ? T(-2) : one(T)) : Bound{T}(nothing) for i in 1:2count])
        @test result.problem.row_upper==(implied ? fill(Bound(T(upper)),count) : [Bound(isodd(i) ? (kind==:nonunit ? T(2) : T(3)) : T(upper)) for i in 1:2count])
        @test result.problem.objective==fill(T(2),count) && result.problem.objective_constant==7
        @test all(record->record.removed_row==implied,only(result.postsolve_stack).records)
        y=kind in (:fixed_positive,:fixed_negative) ? zero(T) : T(1)/2;primal=fill(y,count)
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
    for (kind,limit) in ((:positive,52561),(:negative,53329),(:fixed_positive,38979),(:fixed_negative,39235),(:nonunit,55103),(:free_pivot,29233))
        problem,pass=aggregation_implied_unit_division_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
