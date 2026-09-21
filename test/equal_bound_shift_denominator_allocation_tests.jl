using SparseArrays

@testset "Bound shifts match independent exact subtraction" begin
    values=(-4//1,-1//1,0//1,1//1,4//1,1//2,-1//2,3//2,-3//2)
    shifts=Rational{BigInt}.((-3//1,-1//1,0//1,1//1,3//1,-1//2,1//2,-3//2,3//2,-1//4,1//4))
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), value in values, shift in shifts
        bound=Bound(T(value));original=deepcopy(bound)
        @test JSimplex._shift_bound_exact(T,bound,shift)==Bound(T(value-shift))
        @test isequal(bound,original)
    end
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), shift in shifts
        bound=Bound{T}(nothing)
        @test JSimplex._shift_bound_exact(T,bound,shift)===bound
    end
end

@testset "Equal shift denominators normalize large rationals" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), sign in (-1,1)
        value=T(sign*((BigInt(1)<<300)+1),BigInt(den));bound=Bound(value);original=deepcopy(bound)
        for shift in (T(1,den),T(-1,den),T(2,den),T(-2,den),T(1,den+2),value)
            result=JSimplex._shift_bound_exact(T,bound,shift);exact=value-shift
            @test result==Bound(exact)
            @test denominator(bound_value(result))>0 && gcd(numerator(bound_value(result)),denominator(bound_value(result)))==1
            @test isequal(bound,original)
        end
    end
end

@testset "Equal shift denominators preserve stored BigFloat precision gates" begin
    for sign in (-1,1)
        bound,value,tiny=setprecision(BigFloat,256) do
            tiny=big(1)//(BigInt(1)<<200);value=sign*(big(1)//big(1)+tiny)
            Bound(BigFloat(value)),value,tiny
        end
        original=deepcopy(bound)
        for shift in (tiny,-tiny,tiny/2,zero(tiny),value), ambient in (32,64,256)
            exact=value-shift;accepted=iszero(shift) || iszero(exact) || exact==sign || ambient==256
            setprecision(BigFloat,ambient) do
                result=JSimplex._shift_bound_exact(BigFloat,bound,shift)
                @test isnothing(result)==!accepted
                if accepted
                    actual=setprecision(BigFloat,256) do
                        Rational{BigInt}(bound_value(result))
                    end
                    @test actual==exact
                else
                    @test isequal(bound,original)
                end
                @test isequal(bound,original) && precision(bound_value(bound))==256
            end
        end
    end
    for T in (Float32,Float64)
        for (value,shift) in ((floatmax(T),-Rational{BigInt}(floatmax(T))),
            (one(T)+eps(T),-((BigInt(1)<<(precision(T)+1))+1)//(BigInt(1)<<(precision(T)-1))))
            bound=Bound(value);original=deepcopy(bound)
            @test isnothing(JSimplex._shift_bound_exact(T,bound,shift))
            @test isequal(bound,original)
        end
        bound=Bound(T(-0.0))
        @test isequal(JSimplex._shift_bound_exact(T,bound,big(0)//big(1)),bound)
    end
end

@testset "Sparse aggregation benefits from equal shift denominators" begin
function equal_bound_shift_denominator_probe(kind; count=128, T=Float64)
    pivot=kind in (:negative,:fraction_negative) ? T(-2) : T(2)
    fractional=kind in (:fraction_positive,:fraction_negative,:unequal)
    rhs=kind==:zero_shift ? zero(T) : fractional ? one(T) : T(4)
    factor=fractional ? T(3) : T(6)
    upper=kind in (:fraction_positive,:fraction_negative) ? T(5)/2 : kind==:unequal ? T(2) : T(20)
    rows=collect(1:2:2count);other=rows.+1
    A=sparse(vcat(rows,rows,other,other),vcat(rows,other,rows,other),
        vcat(fill(pivot,count),fill(T(3),count),fill(factor,count),fill(T(5),count)),2count,2count)
    problem=LinearProblem(A,repeat(T[0,2],count);objective_constant=T(7),
        row_lower=[isodd(i) ? rhs : -upper for i in 1:2count],
        row_upper=[isodd(i) ? rhs : upper for i in 1:2count],
        column_lower=fill(nothing,2count),column_upper=fill(nothing,2count))
    return problem,JSimplex.aggregate_sparse_equalities
end
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive,:negative,:fraction_positive,:fraction_negative,:unequal,:zero_shift)
        count=4;problem,pass=equal_bound_shift_denominator_probe(kind;count,T)
        original=deepcopy(problem);result=pass(problem);pivot=problem.A[1,1];rhs=bound_value(problem.row_lower[1]);factor=problem.A[2,1];shift=factor*rhs/pivot
        @test result.problem.A==spdiagm(0=>fill(T(5)-3factor/pivot,count))
        @test result.problem.row_lower==fill(Bound(bound_value(problem.row_lower[2])-shift),count)
        @test result.problem.row_upper==fill(Bound(bound_value(problem.row_upper[2])-shift),count)
        @test result.problem.objective==fill(T(2),count) && result.problem.objective_constant==7
        @test all(record->record.removed_row,only(result.postsolve_stack).records)
        primal=zeros(T,count);restored=JSimplex.postsolve_primal(result,primal)
        @test restored==repeat(T[rhs/pivot,0],count)
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
    for (kind,limit) in ((:positive,34031),(:negative,34031),(:fraction_positive,32879),(:fraction_negative,32879),(:unequal,33399),(:zero_shift,23543))
        problem,pass=equal_bound_shift_denominator_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
