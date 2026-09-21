using SparseArrays

@testset "Exact unit representation preserves supported scalar types" begin
    values=Rational{BigInt}.((-129,-128,-127,-2,-1,0,1,2,127,128,129,-3//2,3//2,-1//3,1//3))
    for T in (Bool,Int8,Int64,Int128,BigInt,Float32,Float64,BigFloat,Rational{BigInt}), value in values
        original=deepcopy(value)
        accepted=T==Bool ? value in (0,1) : T==Int8 ? denominator(value)==1 && -128<=value<=127 :
            T<:Integer ? denominator(value)==1 : T<:AbstractFloat ? denominator(value) in (1,2) : true
        result=JSimplex._represent_exact(T,value)
        @test isnothing(result)==!accepted
        if accepted
            @test result isa T && Rational{BigInt}(result)==value
        else
            @test result===nothing
        end
        @test isequal(value,original)
    end
end

@testset "Unit conversions reject rounded neighbors on both sides" begin
    offsets=(-2,-1,-3//4,-1//2,-1//4,0,1//4,1//2,3//4,1,2)
    for T in (Float32,Float64), sign in (-1,1), offset in offsets
        value=sign*(big(1)//big(1)+offset*Rational{BigInt}(eps(T)));original=deepcopy(value)
        accepted=denominator(offset)==1 || offset==-1//2;result=JSimplex._represent_exact(T,value)
        @test isnothing(result)==!accepted
        @test isnothing(result) || result isa T && Rational{BigInt}(result)==value
        @test isequal(value,original)
    end
    for ambient in (16,32,64,128,256), sign in (-1,1), offset in offsets
        value=sign*(big(1)//big(1)+offset*(big(1)//(BigInt(1)<<(ambient-1))));original=deepcopy(value)
        setprecision(BigFloat,ambient) do
            accepted=denominator(offset)==1 || offset==-1//2;result=JSimplex._represent_exact(BigFloat,value)
            @test isnothing(result)==!accepted
            @test isnothing(result) || Rational{BigInt}(result)==value
            @test isnothing(result) || precision(result)==ambient
            @test isequal(value,original)
        end
    end
end

@testset "Unit shortcuts preserve high precision tails" begin
    for ambient in (32,64,256), sign in (-1,1), direction in (-1,1)
        value=sign*(big(1)//big(1)+direction*(big(1)//(BigInt(1)<<200)));original=deepcopy(value)
        setprecision(BigFloat,ambient) do
            result=JSimplex._represent_exact(BigFloat,value)
            @test isnothing(result)==(ambient<256)
            @test isnothing(result) || JSimplex._exact_rational(result)==value
            @test isnothing(result) || precision(result)==ambient
            @test isequal(value,original)
        end
    end
    for T in (Float32,Float64), sign in (-1,1)
        @test isnothing(JSimplex._represent_exact(T,sign*big(1)//big(3)))
        @test isnothing(JSimplex._represent_exact(T,sign*Rational{BigInt}(nextfloat(zero(T)))/2))
        @test isnothing(JSimplex._represent_exact(T,sign*2Rational{BigInt}(floatmax(T))))
    end
end

@testset "Exact unit results preserve complete doubleton substitutions" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), sign in (-1,1), kind in (:unit_alpha,:unit_cost,:unit_constant,:unit_matrix,:unit_bound,:nonunit)
        pivot=2;rhs=kind==:unit_alpha ? 2sign : 4;alpha=rhs//pivot;beta=-1
        retained_cost=kind==:unit_cost ? sign-2beta : 5;constant=kind==:unit_constant ? sign-2alpha : 7
        old=kind==:unit_matrix ? sign-3beta : 5;bound=kind==:unit_bound ? sign+3alpha : 20
        problem=LinearProblem(sparse(T[pivot 2;3 old]),T[2,retained_cost];objective_constant=T(constant),
            row_lower=T[rhs,bound],row_upper=T[rhs,bound],column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
        original=deepcopy(problem);result=JSimplex.substitute_free_doubleton(problem);step=only(result.postsolve_stack)
        @test step.alpha==T(alpha) && step.beta==T(beta)
        @test result.problem.A==reshape(T[old+3beta],1,1)
        @test result.problem.objective==T[retained_cost+2beta] && result.problem.objective_constant==constant+2alpha
        @test result.problem.row_lower==[Bound(T(bound-3alpha))] && result.problem.row_upper==[Bound(T(bound-3alpha))]
        primal=T[2];restored=JSimplex.postsolve_primal(result,primal)
        @test restored==T[alpha+2beta,2]
        @test problem.objective_constant+sum(problem.objective.*restored)==result.problem.objective_constant+sum(result.problem.objective.*primal)
        basis=JSimplex.Basis([2],[JSimplex.FREE_NONBASIC,JSimplex.BASIC])
        @test JSimplex.restore_basis(result,basis).basic_indices==[1,4]
        result.problem.objective[1]+=one(T);result.problem.A.nzval[1]+=one(T);result.problem.row_upper[1]=Bound(T(20))
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective)
        @test isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Exact unit representation allocation guards" begin
function unit_exact_representation_probe(kind; count=128)
    value=kind==:zero ? big(0)//big(1) : kind==:nonunit ? big(3)//big(2) :
        kind in (:rounded_positive,:rounded_negative) ? big(1)//big(1)+big(1)//(BigInt(1)<<55) : big(1)//big(1)
    kind in (:negative_unit,:rounded_negative) && (value=-value)
    values=fill(value,count)
    pass=values->map(value->JSimplex._represent_exact(Float64,value),values)
    return values,pass
end
    for kind in (:positive_unit,:negative_unit,:rounded_positive,:rounded_negative,:zero,:nonunit)
        values,pass=unit_exact_representation_probe(kind;count=8);original=deepcopy(values);result=pass(values)
        if kind in (:rounded_positive,:rounded_negative)
            @test all(isnothing,result)
        else
            expected=kind==:positive_unit ? 1.0 : kind==:negative_unit ? -1.0 : kind==:zero ? 0.0 : 1.5
            @test result==fill(expected,8)
        end
        @test isequal(values,original)
    end
    for (kind,limit) in ((:positive_unit,1422),(:negative_unit,1422),(:rounded_positive,1422),(:rounded_negative,1422),(:zero,450),(:nonunit,1986))
        values,pass=unit_exact_representation_probe(kind)
        pass(values)
        measured=@timed pass(values)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
