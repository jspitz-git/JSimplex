using SparseArrays

@testset "Implied bounds preserve zero and unbounded endpoint semantics" begin
    intervals=((0,0),(0,2),(-2,0),(nothing,0),(0,nothing),(nothing,nothing),(1,2))
    pairs=((1,1),(2,3),(3,2),(4,1),(1,4),(5,1),(1,5),(6,1),(1,6),(7,2))
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), pivot in (-2,2), coefficients in ((3,1),(-3,1),(3,-1),(-3,-1)), (i,j) in pairs, pivot_bounds in ((1,3),(nothing,3),(1,nothing),(nothing,nothing),(2,2))
        lo1,hi1=intervals[i];lo2,hi2=intervals[j];xlo,xhi=pivot_bounds
        cast(x)=isnothing(x) ? nothing : T(x)
        a,b=coefficients
        problem=LinearProblem(sparse(reshape(T[pivot,a,b],1,3)),zeros(T,3);
            row_lower=T[4],row_upper=T[4],column_lower=cast.([xlo,lo1,lo2]),column_upper=cast.([xhi,hi1,hi2]))
        original=deepcopy(problem)
        terms=[(1,T(pivot)),(2,T(a)),(3,T(b))]
        # For these bounded-size coefficients and pivot bounds, +/-1000
        # witnesses every possible violation caused by an infinite endpoint.
        endpoints(lo,hi)=(isnothing(lo) ? -1000 : lo,isnothing(hi) ? 1000 : hi)
        vertices=[(big(4)-a*y-b*z)//big(pivot) for y in endpoints(lo1,hi1), z in endpoints(lo2,hi2)]
        expected=all(x->(isnothing(xlo) || x>=xlo) && (isnothing(xhi) || x<=xhi),vertices)
        @test JSimplex._equality_implies_column_bounds(problem,terms,1,JSimplex._exact_rational(T(pivot)),JSimplex._exact_rational(T(4)))==expected
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
    end
end

@testset "Tiny stored nonzero endpoints still constrain implied bounds" begin
    for side in (:lower,:upper), tiny in (false,true), direction in (-1,1), ambient in (32,64,256)
        problem=setprecision(BigFloat,256) do
            epsilon=tiny ? BigFloat(2)^(-200) : zero(BigFloat)
            rawlo,rawhi=side==:lower ? (zero(BigFloat),epsilon) : (-epsilon,zero(BigFloat))
            lo,hi=direction>0 ? (rawlo,rawhi) : (-rawhi,-rawlo)
            LinearProblem(sparse(BigFloat[2 direction;6 5]),BigFloat[0,2];objective_constant=BigFloat(7),
                row_lower=[BigFloat(4),nothing],row_upper=BigFloat[4,100],
                column_lower=[side==:lower ? BigFloat(2) : nothing,lo],
                column_upper=[side==:upper ? BigFloat(2) : nothing,hi])
        end
        original=deepcopy(problem);saved=JSimplex._exact_rational.(bound_value.([problem.column_lower[2],problem.column_upper[2]]))
        setprecision(BigFloat,ambient) do
            terms=JSimplex._row_entries(problem.A)[1]
            @test JSimplex._equality_implies_column_bounds(problem,terms,1,big(2)//big(1),big(4)//big(1))==!tiny
            result=JSimplex.aggregate_sparse_equalities(problem)
            @test size(result.problem.A)==(tiny ? 2 : 1,1)
            @test only(only(result.postsolve_stack).records).removed_row==!tiny
            @test result.problem.objective==BigFloat[2] && result.problem.objective_constant==7
            @test JSimplex.postsolve_primal(result,BigFloat[0])==BigFloat[2,0]
            @test JSimplex._exact_rational.(bound_value.([problem.column_lower[2],problem.column_upper[2]]))==saved
            @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
        end
    end
end

@testset "Signed zero bounds imply the same projected interval" begin
    for T in (Float32,Float64,BigFloat), negative in (false,true), pivot in (-2,2), term in (-3,3)
        z=negative ? -zero(T) : zero(T)
        problem=LinearProblem(sparse(T[pivot term;6 5]),T[0,2];row_lower=T[4,-100],row_upper=T[4,100],
            column_lower=T[-3,z],column_upper=T[3,z])
        original=deepcopy(problem);terms=JSimplex._row_entries(problem.A)[1]
        @test JSimplex._equality_implies_column_bounds(problem,terms,1,JSimplex._exact_rational(T(pivot)),big(4)//big(1))
        result=JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A)==(1,1)
        @test JSimplex.postsolve_primal(result,T[0])==T[4/pivot,0]
        @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
    end
end

@testset "Sparse aggregation skips zero endpoints in implied-bound activities" begin
function aggregation_implied_zero_bounds_probe(kind; count=128, T=Float64)
    term=kind==:fixed_negative ? T(-3) : T(3)
    low=kind==:upper_zero ? T(-2) : kind==:nonzero_bounds ? T(1)/2 : zero(T)
    high=kind==:lower_zero ? T(2) : kind==:nonzero_bounds ? one(T) : zero(T)
    odd=collect(1:2:2count);even=odd.+1
    A=sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(T(2),count),fill(term,count),fill(T(6),count),fill(T(5),count)),2count,2count)
    problem=LinearProblem(A,[isodd(i) ? zero(T) : T(2) for i in 1:2count];objective_constant=T(7),
        row_lower=[isodd(i) ? T(4) : nothing for i in 1:2count],
        row_upper=[isodd(i) ? T(4) : T(100) for i in 1:2count],
        column_lower=[isodd(i) ? (kind==:free_pivot ? nothing : one(T)) : low for i in 1:2count],
        column_upper=[isodd(i) ? (kind==:free_pivot ? nothing : T(3)) : high for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:fixed_positive,:fixed_negative,:lower_zero,:upper_zero,:nonzero_bounds,:free_pivot)
        count=4;problem,pass=aggregation_implied_zero_bounds_probe(kind;count,T)
        original=deepcopy(problem);result=pass(problem)
        implied=kind in (:fixed_positive,:fixed_negative,:free_pivot)
        term=problem.A[1,2]
        expected=implied ? spdiagm(0=>fill(T(5)-3term,count)) :
            sparse(collect(1:2count),repeat(collect(1:count),inner=2),repeat(T[term,5-3term],count),2count,count)
        @test result.problem.A==expected
        @test result.problem.row_lower==(implied ? fill(Bound{T}(nothing),count) : [isodd(i) ? Bound(T(-2)) : Bound{T}(nothing) for i in 1:2count])
        @test result.problem.row_upper==(implied ? fill(Bound(T(88)),count) : [Bound(isodd(i) ? T(2) : T(88)) for i in 1:2count])
        @test result.problem.objective==fill(T(2),count) && result.problem.objective_constant==7
        @test all(record->record.removed_row==implied,only(result.postsolve_stack).records)
        y=kind==:nonzero_bounds ? T(1)/2 : zero(T);primal=fill(y,count)
        restored=JSimplex.postsolve_primal(result,primal)
        @test restored==repeat(T[(4-term*y)/2,y],count)
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
    for (kind,limit) in ((:fixed_positive,48067),(:fixed_negative,48067),(:lower_zero,59729),(:upper_zero,59729),(:nonzero_bounds,62783),(:free_pivot,29873))
        problem,pass=aggregation_implied_zero_bounds_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
