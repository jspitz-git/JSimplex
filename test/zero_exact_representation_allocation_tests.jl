using SparseArrays

@testset "Exact representation preserves zero and supported scalar types" begin
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

@testset "Zero conversions cannot accept nonzero subnormal rounding" begin
    for T in (Float32,Float64), sign in (-1,1), scale in (0,1//4,1//2,3//4,1,3//2,2,3)
        value=sign*Rational{BigInt}(nextfloat(zero(T)))*scale;original=deepcopy(value)
        accepted=denominator(scale)==1;result=JSimplex._represent_exact(T,value)
        @test isnothing(result)==!accepted
        if accepted
            @test Rational{BigInt}(result)==value
            @test !iszero(value) || !signbit(result)
        else
            @test result===nothing
            @test !iszero(value)
        end
        @test isequal(value,original)
    end
    for T in (Float32,Float64), sign in (-1,1)
        maximum=sign*Rational{BigInt}(floatmax(T))
        @test JSimplex._represent_exact(T,maximum)==sign*floatmax(T)
        @test isnothing(JSimplex._represent_exact(T,2maximum))
        tail=sign*(big(1)//big(1)+Rational{BigInt}(eps(T))/2)
        @test isnothing(JSimplex._represent_exact(T,tail))
    end
end

@testset "Exact zero conversion retains ambient BigFloat precision" begin
    for ambient in (32,64,256)
        setprecision(BigFloat,ambient) do
            result=JSimplex._represent_exact(BigFloat,big(0)//big(1))
            @test result isa BigFloat && iszero(result) && !signbit(result)
            @test precision(result)==ambient
            for sign in (-1,1)
                tiny=sign*big(1)//(BigInt(1)<<200)
                @test JSimplex._exact_rational(JSimplex._represent_exact(BigFloat,tiny))==tiny
                for value in (sign*(big(1)//big(1)+big(1)//(BigInt(1)<<200)),sign*((BigInt(1)<<200)+1)//big(1))
                    original=deepcopy(value);represented=JSimplex._represent_exact(BigFloat,value)
                    @test isnothing(represented)==(ambient<256)
                    @test ambient<256 || JSimplex._exact_rational(represented)==value
                    @test isequal(value,original)
                end
            end
        end
    end
end

@testset "Zero exact results preserve complete doubleton substitutions" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), pivot in (-2,2), kind in (:zero_alpha,:zero_cost,:zero_constant,:zero_matrix,:zero_bound,:nonzero)
        rhs=kind==:zero_alpha ? 0 : 4;alpha=rhs//pivot;beta=-2//pivot
        retained_cost=kind==:zero_cost ? -2beta : 5;constant=kind==:zero_constant ? -2alpha : 7
        old=kind==:zero_matrix ? -3beta : 5;bound=kind==:zero_bound ? 3alpha : 20
        problem=LinearProblem(sparse(T[pivot 2;3 old]),T[2,retained_cost];objective_constant=T(constant),
            row_lower=T[rhs,bound],row_upper=T[rhs,bound],column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
        original=deepcopy(problem);result=JSimplex.substitute_free_doubleton(problem);step=only(result.postsolve_stack)
        @test step.alpha==T(alpha) && step.beta==T(beta)
        @test result.problem.A==reshape(T[old+3beta],1,1)
        @test nnz(result.problem.A)==(kind==:zero_matrix ? 0 : 1)
        @test result.problem.objective==T[retained_cost+2beta] && result.problem.objective_constant==constant+2alpha
        @test result.problem.row_lower==[Bound(T(bound-3alpha))] && result.problem.row_upper==[Bound(T(bound-3alpha))]
        primal=T[2];restored=JSimplex.postsolve_primal(result,primal)
        @test restored==T[alpha+2beta,2]
        @test problem.objective_constant+sum(problem.objective.*restored)==result.problem.objective_constant+sum(result.problem.objective.*primal)
        basis=JSimplex.Basis([2],[JSimplex.FREE_NONBASIC,JSimplex.BASIC])
        @test JSimplex.restore_basis(result,basis).basic_indices==[1,4]
        result.problem.objective[1]+=one(T);result.problem.row_upper[1]=Bound(T(20))
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective)
        @test isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Exact zero representation allocation guards" begin
function zero_exact_representation_probe(kind; count=128)
    T=kind in (:zero_float32,:underflow_float32) ? Float32 : Float64
    value=kind in (:zero_float32,:zero_float64) ? big(0)//big(1) :
        kind==:underflow_float32 ? big(1)//(BigInt(1)<<151) :
        kind==:underflow_float64 ? big(1)//(BigInt(1)<<1076) :
        kind==:nonzero ? big(3)//big(2) : big(1)//big(3)
    values=[isodd(i) ? value : -value for i in 1:count]
    pass=values->map(value->JSimplex._represent_exact(T,value),values)
    return values,pass
end
    for kind in (:zero_float32,:zero_float64,:underflow_float32,:underflow_float64,:nonzero,:inexact_nonzero)
        values,pass=zero_exact_representation_probe(kind;count=8);original=deepcopy(values);result=pass(values)
        if kind in (:zero_float32,:zero_float64)
            T=kind==:zero_float32 ? Float32 : Float64
            @test result==zeros(T,8) && all(x->x isa T && !signbit(x),result)
        elseif kind==:nonzero
            @test result==[isodd(i) ? 1.5 : -1.5 for i in 1:8]
        else
            @test all(isnothing,result)
        end
        @test isequal(values,original)
    end
    for (kind,limit) in ((:zero_float32,1038),(:zero_float64,1038),(:underflow_float32,1038),(:underflow_float64,1038),(:nonzero,1986),(:inexact_nonzero,1986))
        values,pass=zero_exact_representation_probe(kind)
        pass(values)
        measured=@timed pass(values)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
