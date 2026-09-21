using SparseArrays

@testset "Implied signed-unit products match endpoint enumeration" begin
    cases=((1,2,3,3,1),(-1,2,3,-3,1),(3,1,1,1,-1),(3,-1,-1,-1,-1),(-3,-1,1,1,1),(1,-3,-1,-1,1),(-1,-3,-1,3,-1),(3,1//2,3//2,-1,0),(1,nothing,1,3,1),(-1,-1,nothing,-3,1),(3,0,0,1,1),(-3,1,1,-1,1))
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), pivot in (-2,2), (a,lo,hi,b,z) in cases, xbounds in ((-4,4),(1,3),(nothing,3),(-4,nothing),(nothing,nothing))
        xlo,xhi=xbounds;cast(x)=isnothing(x) ? nothing : T(x)
        problem=LinearProblem(sparse(reshape(T[pivot,a,b],1,3)),zeros(T,3);
            row_lower=T[4],row_upper=T[4],column_lower=cast.([xlo,lo,z]),column_upper=cast.([xhi,hi,z]))
        original=deepcopy(problem)
        # +/-1000 are sufficient witnesses for the bounded-size coefficients
        # and finite pivot bounds in these fixtures.
        endpoints=(isnothing(lo) ? -1000 : lo,isnothing(hi) ? 1000 : hi)
        vertices=[(big(4)//big(1)-a*y-b*z)/pivot for y in endpoints]
        expected=all(x->(isnothing(xlo) || x>=xlo) && (isnothing(xhi) || x<=xhi),vertices)
        @test JSimplex._equality_implies_column_bounds(problem,JSimplex._row_entries(problem.A)[1],1,JSimplex._exact_rational(T(pivot)),big(4)//big(1))==expected
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
    end
end

@testset "Implied products distinguish stored neighbors of signed units" begin
    for side in (:coefficient,:bound), near in (false,true), direction in (-1,1), ambient in (32,64,256)
        problem=setprecision(BigFloat,256) do
            value=direction*(BigFloat(1)+(near ? BigFloat(2)^(-200) : zero(BigFloat)))
            coefficient,bound=side==:coefficient ? (value,BigFloat(3)) : (BigFloat(3),value)
            rhs=BigFloat(4+3direction)
            LinearProblem(sparse(reshape(BigFloat[2,coefficient],1,2)),zeros(BigFloat,2);
                row_lower=[rhs],row_upper=[rhs],
                column_lower=[direction>0 ? BigFloat(2) : nothing,bound],
                column_upper=[direction<0 ? BigFloat(2) : nothing,bound])
        end
        original=deepcopy(problem);saved_matrix=JSimplex._exact_rational.(problem.A.nzval)
        saved_bound=JSimplex._exact_rational(bound_value(problem.column_lower[2]))
        rhs=JSimplex._exact_rational(bound_value(problem.row_lower[1]))
        setprecision(BigFloat,ambient) do
            @test JSimplex._equality_implies_column_bounds(problem,JSimplex._row_entries(problem.A)[1],1,big(2)//big(1),rhs)==!near
            @test JSimplex._exact_rational.(problem.A.nzval)==saved_matrix
            @test JSimplex._exact_rational(bound_value(problem.column_lower[2]))==saved_bound
            @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
        end
    end
end

@testset "Implied signed-unit products preserve large rational thresholds" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), direction in (-1,1), side in (:coefficient,:bound), offset in (0,1)
        value=T((BigInt(1)<<300)+1,BigInt(den))
        coefficient,bound=side==:coefficient ? (T(direction),value) : (value,T(direction))
        x=(T(4)-coefficient*bound)/2
        problem=LinearProblem(sparse(reshape(T[2,coefficient],1,2)),zeros(T,2);
            row_lower=T[4],row_upper=T[4],column_lower=T[x+offset,bound],column_upper=T[x+offset,bound])
        original=deepcopy(problem)
        @test JSimplex._equality_implies_column_bounds(problem,JSimplex._row_entries(problem.A)[1],1,T(2),T(4))==(offset==0)
        @test problem.A.nzval==original.A.nzval && problem.column_lower==original.column_lower
        @test problem.column_upper==original.column_upper
    end
end

@testset "Sparse aggregation skips signed-unit implied-bound multiplication" begin
function aggregation_implied_unit_products_probe(kind; count=128, T=Float64)
    term=kind==:coefficient_positive ? one(T) : kind==:coefficient_negative ? -one(T) : T(3)
    low=kind==:bound_positive ? one(T) : kind==:bound_negative ? -one(T) : kind==:zero_bounds ? zero(T) : kind==:nonunit ? T(1)/2 : T(2)
    high=kind in (:bound_positive,:bound_negative,:zero_bounds) ? low : kind==:nonunit ? T(3)/2 : T(3)
    wide=kind in (:bound_positive,:bound_negative)
    odd=collect(1:2:2count);even=odd.+1
    A=sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(T(2),count),fill(term,count),fill(T(6),count),fill(T(5),count)),2count,2count)
    problem=LinearProblem(A,[isodd(i) ? zero(T) : T(2) for i in 1:2count];objective_constant=T(7),
        row_lower=[isodd(i) ? T(4) : nothing for i in 1:2count],
        row_upper=[isodd(i) ? T(4) : T(100) for i in 1:2count],
        column_lower=[isodd(i) ? (wide ? T(-4) : one(T)) : low for i in 1:2count],
        column_upper=[isodd(i) ? (wide ? T(4) : T(3)) : high for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:coefficient_positive,:coefficient_negative,:bound_positive,:bound_negative,:nonunit,:zero_bounds)
        count=4;problem,pass=aggregation_implied_unit_products_probe(kind;count,T)
        original=deepcopy(problem);result=pass(problem)
        implied=kind in (:bound_positive,:bound_negative,:zero_bounds)
        term=problem.A[1,2]
        expected=implied ? spdiagm(0=>fill(T(5)-3term,count)) :
            sparse(collect(1:2count),repeat(collect(1:count),inner=2),repeat(T[term,5-3term],count),2count,count)
        @test result.problem.A==expected
        @test result.problem.row_lower==(implied ? fill(Bound{T}(nothing),count) : [isodd(i) ? Bound(T(-2)) : Bound{T}(nothing) for i in 1:2count])
        @test result.problem.row_upper==(implied ? fill(Bound(T(88)),count) : [Bound(isodd(i) ? T(2) : T(88)) for i in 1:2count])
        @test result.problem.objective==fill(T(2),count) && result.problem.objective_constant==7
        @test all(record->record.removed_row==implied,only(result.postsolve_stack).records)
        y=bound_value(problem.column_lower[2]);primal=fill(y,count)
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
    for (kind,limit) in ((:coefficient_positive,57809),(:coefficient_negative,58065),(:bound_positive,48835),(:bound_negative,48835),(:nonunit,60479),(:zero_bounds,42673))
        problem,pass=aggregation_implied_unit_products_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
