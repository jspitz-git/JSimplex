using SparseArrays

@testset "Cancelled inferred bounds match endpoint enumeration" begin
    # Endpoint enumeration detects a swapped minimum/maximum, a lost nonzero
    # activity, or a skipped division by the signed pivot.
    cases=((3,1,1,1,0),(3,0,1,1,0),(3,1,2,1,0),
           (3,1,1,-3,1),(-3,1,1,3,1),(-3,1,1,1,0),
           (3,0,1,-3,1),(1,nothing,0,3,0),(-1,0,nothing,3,0),
           (3,1//2,1,1,0))
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

@testset "Cancelled candidates retain tiny RHS and activity differences" begin
    for source in (:rhs,:activity), direction in (-1,1), near in (false,true), pivot in (-2,-1,1,2), ambient in (32,64,256)
        problem=setprecision(BigFloat,256) do
            delta=near ? direction*BigFloat(2)^(-200) : zero(BigFloat)
            rhs=source==:rhs ? BigFloat(3)+delta : BigFloat(3)
            coefficient=source==:activity ? BigFloat(3)+delta : BigFloat(3)
            LinearProblem(sparse(reshape(BigFloat[pivot,coefficient],1,2)),zeros(BigFloat,2);
                row_lower=[rhs],row_upper=[rhs],column_lower=BigFloat[0,1],column_upper=BigFloat[0,1])
        end
        original=deepcopy(problem);rhs=JSimplex._exact_rational(bound_value(problem.row_lower[1]))
        setprecision(BigFloat,ambient) do
            @test JSimplex._equality_implies_column_bounds(problem,JSimplex._row_entries(problem.A)[1],1,big(pivot)//big(1),rhs)==!near
            @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower)
            @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
        end
    end
end

@testset "Cancelled candidates compare exact signed bounds to zero" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), pivot in (-2,-1,1,2), lower in (false,true), direction in (-1,0,1)
        tiny=T==Float32 ? T(2)^(-120) : T==Float64 ? T(2)^(-1000) : T==BigFloat ? T(2)^(-300) : T(1,BigInt(1)<<300)
        bound=direction*tiny
        problem=LinearProblem(sparse(reshape(T[pivot,3],1,2)),zeros(T,2);
            row_lower=T[3],row_upper=T[3],column_lower=[lower ? bound : nothing,T(1)],
            column_upper=[lower ? nothing : bound,T(1)])
        @test JSimplex._equality_implies_column_bounds(problem,JSimplex._row_entries(problem.A)[1],1,big(pivot)//big(1),big(3)//big(1))==(lower ? direction<=0 : direction>=0)
    end
end

@testset "Large rational activities cancel without losing a residual" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), pivot in (-2,2), direction in (-1,1), offset in (0,1)
        value=T(direction*((BigInt(1)<<300)+1),BigInt(den));rhs=value+T(offset,BigInt(1)<<350)
        problem=LinearProblem(sparse(reshape(T[pivot,value],1,2)),zeros(T,2);
            row_lower=T[rhs],row_upper=T[rhs],column_lower=T[0,1],column_upper=T[0,1])
        @test JSimplex._equality_implies_column_bounds(problem,JSimplex._row_entries(problem.A)[1],1,T(pivot),rhs)==(offset==0)
    end
end

@testset "Sparse aggregation bypasses cancelled inferred-bound arithmetic" begin
function aggregation_implied_cancelled_candidates_probe(kind; count=128, T=Float64)
    pivot=kind==:negative ? T(-2) : T(2)
    low=kind==:lower_cancel ? zero(T) : kind==:noncancel ? T(1)/2 : one(T)
    high=kind==:upper_cancel ? T(2) : kind==:noncancel ? T(3)/4 : one(T)
    xlo=kind==:free_pivot ? nothing : kind==:lower_cancel ? zero(T) : -one(T)
    xhi=kind==:free_pivot ? nothing : kind==:upper_cancel ? zero(T) : one(T)
    odd=collect(1:2:2count);even=odd.+1
    A=sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(pivot,count),fill(T(3),count),fill(T(6),count),fill(T(5),count)),2count,2count)
    problem=LinearProblem(A,[isodd(i) ? zero(T) : T(2) for i in 1:2count];objective_constant=T(7),
        row_lower=[isodd(i) ? T(3) : nothing for i in 1:2count],
        row_upper=[isodd(i) ? T(3) : T(100) for i in 1:2count],
        column_lower=[isodd(i) ? xlo : low for i in 1:2count],
        column_upper=[isodd(i) ? xhi : high for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive,:negative,:lower_cancel,:upper_cancel,:noncancel,:free_pivot)
        count=4;problem,pass=aggregation_implied_cancelled_candidates_probe(kind;count,T)
        original=deepcopy(problem);result=pass(problem)
        implied=kind in (:positive,:negative,:noncancel,:free_pivot)
        term=problem.A[1,2];pivot=problem.A[1,1];multiplier=6/pivot;upper=100-3multiplier
        expected=implied ? spdiagm(0=>fill(T(5)-multiplier*term,count)) :
            sparse(collect(1:2count),repeat(collect(1:count),inner=2),repeat(T[term,5-multiplier*term],count),2count,count)
        @test result.problem.A==expected
        @test result.problem.row_lower==(implied ? fill(Bound{T}(nothing),count) : [isodd(i) ? Bound(kind==:lower_cancel ? one(T) : T(3)) : Bound{T}(nothing) for i in 1:2count])
        @test result.problem.row_upper==(implied ? fill(Bound(T(upper)),count) : [Bound(isodd(i) ? (kind==:lower_cancel ? T(3) : T(5)) : T(upper)) for i in 1:2count])
        @test result.problem.objective==fill(T(2),count) && result.problem.objective_constant==7
        @test all(record->record.removed_row==implied,only(result.postsolve_stack).records)
        y=kind==:noncancel ? T(1)/2 : one(T);primal=fill(y,count)
        restored=JSimplex.postsolve_primal(result,primal)
        @test restored==repeat(T[(3-term*y)/pivot,y],count)
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
    for (kind,limit) in ((:positive,44483),(:negative,44483),(:lower_cancel,49745),(:upper_cancel,53841),(:noncancel,49585),(:free_pivot,29873))
        problem,pass=aggregation_implied_cancelled_candidates_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
