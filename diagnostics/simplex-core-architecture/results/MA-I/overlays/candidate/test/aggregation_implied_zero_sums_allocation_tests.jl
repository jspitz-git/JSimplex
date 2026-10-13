using SparseArrays

@testset "Implied activities reuse zero after prefix cancellation" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), pivot in (-2,2), a in (-3,-1//2,1//2,3), b in (-3,3), yhigh in (1,2), wbounds in ((0,2),(-2,0),(1//2,1)), xbounds in ((-4,4),(1,3),(nothing,3))
        wlo,whi=wbounds;xlo,xhi=xbounds
        cast(x)=isnothing(x) ? nothing : T(x)
        problem=LinearProblem(sparse(reshape(T[pivot,a,-a,b],1,4)),zeros(T,4);
            row_lower=T[4],row_upper=T[4],column_lower=cast.([xlo,1,1,wlo]),column_upper=cast.([xhi,yhigh,1,whi]))
        original=deepcopy(problem);terms=JSimplex._row_entries(problem.A)[1]
        # Enumerate endpoints independently; fixed y=z=1 cancels the prefix,
        # while yhigh=2 leaves only one activity extreme at zero.
        vertices=[(big(4)-a*y+a-b*w)/pivot for y in (1,yhigh), w in (wlo,whi)]
        expected=all(x->(isnothing(xlo) || x>=xlo) && x<=xhi,vertices)
        @test JSimplex._equality_implies_column_bounds(problem,terms,1,JSimplex._exact_rational(T(pivot)),big(4)//big(1))==expected
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
    end
end

@testset "Stored precision survives zero-prefix reuse" begin
    for side in (:lower,:upper), tiny in (false,true), direction in (-1,1), ambient in (32,64,256)
        problem=setprecision(BigFloat,256) do
            epsilon=BigFloat(2)^(-200);coefficient=BigFloat(3)+epsilon
            extent=tiny ? epsilon : zero(BigFloat)
            rawlo,rawhi=side==:lower ? (zero(BigFloat),extent) : (-extent,zero(BigFloat))
            lo,hi=direction>0 ? (rawlo,rawhi) : (-rawhi,-rawlo)
            LinearProblem(sparse(reshape(BigFloat[2,coefficient,-coefficient,direction],1,4)),zeros(BigFloat,4);
                row_lower=BigFloat[4],row_upper=BigFloat[4],
                column_lower=[side==:lower ? BigFloat(2) : nothing,BigFloat(1),BigFloat(1),lo],
                column_upper=[side==:upper ? BigFloat(2) : nothing,BigFloat(1),BigFloat(1),hi])
        end
        original=deepcopy(problem);saved=JSimplex._exact_rational.(problem.A.nzval)
        setprecision(BigFloat,ambient) do
            @test JSimplex._equality_implies_column_bounds(problem,JSimplex._row_entries(problem.A)[1],1,big(2)//big(1),big(4)//big(1))==!tiny
            @test JSimplex._exact_rational.(problem.A.nzval)==saved
            @test all(precision(x)==256 for x in problem.A.nzval)
            @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
        end
    end
end

@testset "Zero-sum reuse never revives unbounded activity" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), side in (:lower,:upper), direction in (-1,1), unbounded_first in (false,true)
        terms=unbounded_first ? T[2,direction,3,-3] : T[2,3,-3,direction]
        lows=unbounded_first ? Union{Nothing,T}[nothing,1,1] : Union{Nothing,T}[1,1,nothing]
        highs=unbounded_first ? Union{Nothing,T}[nothing,1,1] : Union{Nothing,T}[1,1,nothing]
        problem=LinearProblem(sparse(reshape(terms,1,4)),zeros(T,4);row_lower=T[4],row_upper=T[4],
            column_lower=[side==:lower ? T(2) : nothing;lows],column_upper=[side==:upper ? T(2) : nothing;highs])
        @test !JSimplex._equality_implies_column_bounds(problem,JSimplex._row_entries(problem.A)[1],1,big(2)//big(1),big(4)//big(1))
    end
end

@testset "Sparse aggregation skips addition to zero implied activities" begin
function aggregation_implied_zero_sums_probe(kind; count=128, T=Float64)
    term=kind==:negative ? T(-3) : T(3)
    low=kind in (:lower_zero,:zero_bounds) ? zero(T) : kind==:upper_zero ? T(-2) : T(1)/2
    high=kind in (:upper_zero,:zero_bounds) ? zero(T) : kind==:lower_zero ? T(2) : one(T)
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
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive,:negative,:lower_zero,:upper_zero,:zero_bounds,:free_pivot)
        count=4;problem,pass=aggregation_implied_zero_sums_probe(kind;count,T)
        original=deepcopy(problem);result=pass(problem)
        implied=kind in (:zero_bounds,:free_pivot)
        term=problem.A[1,2]
        expected=implied ? spdiagm(0=>fill(T(5)-3term,count)) :
            sparse(collect(1:2count),repeat(collect(1:count),inner=2),repeat(T[term,5-3term],count),2count,count)
        @test result.problem.A==expected
        @test result.problem.row_lower==(implied ? fill(Bound{T}(nothing),count) : [isodd(i) ? Bound(T(-2)) : Bound{T}(nothing) for i in 1:2count])
        @test result.problem.row_upper==(implied ? fill(Bound(T(88)),count) : [Bound(isodd(i) ? T(2) : T(88)) for i in 1:2count])
        @test result.problem.objective==fill(T(2),count) && result.problem.objective_constant==7
        @test all(record->record.removed_row==implied,only(result.postsolve_stack).records)
        y=kind in (:positive,:negative,:free_pivot) ? T(1)/2 : zero(T);primal=fill(y,count)
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
    for (kind,limit) in ((:positive,62033),(:negative,62033),(:lower_zero,56657),(:upper_zero,56657),(:zero_bounds,42673),(:free_pivot,29873))
        problem,pass=aggregation_implied_zero_sums_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
