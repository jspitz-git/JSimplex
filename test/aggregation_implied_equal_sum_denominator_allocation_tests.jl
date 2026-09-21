using SparseArrays

@testset "Shared-denominator activity sums match endpoint enumeration" begin
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

@testset "Activity sums preserve stored BigFloat low bits" begin
    for pivot in (-2,2), direction in (-1,1), offset in (-1,0,1), ambient in (32,64,256)
        problem=setprecision(BigFloat,256) do
            tiny=BigFloat(2)^(-200)
            a=direction*(BigFloat(3)+tiny);b=direction*(BigFloat(5)-tiny)+offset*tiny
            rhs=BigFloat(2+8direction);x=BigFloat(2)/pivot
            LinearProblem(sparse(reshape(BigFloat[pivot,a,b],1,3)),zeros(BigFloat,3);
                row_lower=[rhs],row_upper=[rhs],column_lower=BigFloat[x,1,1],column_upper=BigFloat[x,1,1])
        end
        original=deepcopy(problem);rhs=JSimplex._exact_rational(bound_value(problem.row_lower[1]))
        setprecision(BigFloat,ambient) do
            @test JSimplex._equality_implies_column_bounds(problem,JSimplex._row_entries(problem.A)[1],1,big(pivot)//big(1),rhs)==(offset==0)
            @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower)
            @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
        end
    end
end

@testset "Activity sums reduce large rational numerators" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), direction in (-1,1), pivot in (-2,2), offset in (0,1)
        large=BigInt(1)<<300
        a=T(direction*(large*den+1),BigInt(den));b=T(direction*(7den-1),BigInt(den))
        rhs=T(2+direction*(large+7));x=T(2,pivot)
        problem=LinearProblem(sparse(reshape(T[pivot,a,b],1,3)),zeros(T,3);
            row_lower=T[rhs],row_upper=T[rhs],column_lower=T[x+offset,1,1],column_upper=T[x+offset,1,1])
        original=deepcopy(problem)
        @test JSimplex._equality_implies_column_bounds(problem,JSimplex._row_entries(problem.A)[1],1,T(pivot),rhs)==(offset==0)
        @test problem.A.nzval==original.A.nzval && problem.row_lower==original.row_lower
    end
end

@testset "Sparse aggregation adds shared-denominator activity numerators" begin
function aggregation_implied_equal_sum_denominator_probe(kind; count=128, T=Float64)
    fractional=kind in (:fraction_positive,:fraction_negative,:unequal)
    direction=kind in (:integer_negative,:fraction_negative) ? -one(T) : one(T)
    a=direction*(fractional ? T(1)/2 : T(3))
    b=kind==:unequal ? T(1)/4 : direction*(fractional ? T(3)/2 : T(5))
    xlo=kind==:free_pivot ? nothing : T(-8)
    xhi=kind==:free_pivot ? nothing : T(8)
    rows=collect(1:2:2count);other=rows.+1;cols=collect(1:3:3count)
    A=sparse(vcat(rows,rows,rows,other,other,other),vcat(cols,cols.+1,cols.+2,cols,cols.+1,cols.+2),
        vcat(fill(T(2),count),fill(a,count),fill(b,count),fill(T(6),count),fill(T(5),count),fill(T(7),count)),2count,3count)
    problem=LinearProblem(A,repeat(T[0,2,3],count);objective_constant=T(7),
        row_lower=[isodd(i) ? T(4) : nothing for i in 1:2count],
        row_upper=[isodd(i) ? T(4) : T(100) for i in 1:2count],
        column_lower=[i%3==1 ? xlo : one(T) for i in 1:3count],
        column_upper=[i%3==1 ? xhi : one(T) for i in 1:3count])
    return problem,JSimplex.aggregate_sparse_equalities
end
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:integer_positive,:integer_negative,:fraction_positive,:fraction_negative,:unequal,:free_pivot)
        count=4;problem,pass=aggregation_implied_equal_sum_denominator_probe(kind;count,T)
        original=deepcopy(problem);result=pass(problem);a=problem.A[1,2];b=problem.A[1,3]
        expected=sparse(repeat(collect(1:count),inner=2),collect(1:2count),repeat(T[5-3a,7-3b],count),count,2count)
        @test result.problem.A==expected
        @test result.problem.row_lower==fill(Bound{T}(nothing),count)
        @test result.problem.row_upper==fill(Bound(T(88)),count)
        @test result.problem.objective==repeat(T[2,3],count) && result.problem.objective_constant==7
        @test all(record->record.removed_row,only(result.postsolve_stack).records)
        primal=ones(T,2count);restored=JSimplex.postsolve_primal(result,primal)
        @test restored==repeat(T[(4-a-b)/2,1,1],count)
        @test problem.objective_constant+sum(problem.objective.*restored)==result.problem.objective_constant+sum(result.problem.objective.*primal)
        m,n=size(result.problem.A)
        for state in (JSimplex.AT_LOWER,JSimplex.AT_UPPER)
            basis=JSimplex.Basis(collect(n+1:n+m),[fill(state,n);fill(JSimplex.BASIC,m)])
            restored_basis=JSimplex.restore_basis(result,basis)
            @test restored_basis.basic_indices==[isodd(i) ? 3*((i-1)÷2)+1 : 3count+i for i in 1:2count]
            @test restored_basis.states[[i for i in 1:3count if i%3!=1]]==fill(state,2count)
        end
        result.problem.objective[1]+=one(T);result.problem.A.nzval[1]+=one(T)
        result.problem.row_upper[1]=Bound(T(20))
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective)
        @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
        @test isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
    for (kind,limit) in ((:integer_positive,66543),(:integer_negative,66543),(:fraction_positive,66799),(:fraction_negative,66799),(:unequal,70221),(:free_pivot,44365))
        problem,pass=aggregation_implied_equal_sum_denominator_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
