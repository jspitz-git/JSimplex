using SparseArrays

@testset "Doubleton equal-denominator ratios match exact substitution" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), pivot in (-2,-1//2,1//2,2), retained in (-3,-5//2,5//2,3), rhs in (-4,-3//2,0,3//2,4)
        problem=LinearProblem(sparse(T[pivot retained;3 2]),T[2,3];objective_constant=T(7),
            row_lower=T[rhs,-100],row_upper=T[rhs,100],column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
        original=deepcopy(problem);result=JSimplex.substitute_free_doubleton(problem)
        alpha=Rational{BigInt}(rhs)/Rational{BigInt}(pivot);beta=-Rational{BigInt}(retained)/Rational{BigInt}(pivot)
        step=only(result.postsolve_stack)
        @test step.alpha==T(alpha) && step.beta==T(beta)
        @test result.problem.A==reshape(T[2+3beta],1,1)
        @test result.problem.objective==T[3+2beta] && result.problem.objective_constant==T(7+2alpha)
        @test result.problem.row_lower==[Bound(T(-100-3alpha))] && result.problem.row_upper==[Bound(T(100-3alpha))]
        @test JSimplex.postsolve_primal(result,T[2])==T[alpha+2beta,2]
        basis=JSimplex.Basis([2],[JSimplex.FREE_NONBASIC,JSimplex.BASIC])
        @test JSimplex.restore_basis(result,basis).basic_indices==[1,4]
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
        @test isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant)
    end
end

@testset "Doubleton equal ratio denominators retain canonical large rationals" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), sign in (-1,1), mode in (:general,:cancelled)
        n=BigInt(1)<<300;pivot=T(sign*(n+1),den)
        rhs=mode==:general ? T(n+3,den) : pivot
        retained=mode==:general ? T(n+7,den) : -pivot
        problem=LinearProblem(sparse(reshape(T[pivot,retained],1,2)),T[2,3];objective_constant=T(7),
            row_lower=T[rhs],row_upper=T[rhs],column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
        original=deepcopy(problem);result=JSimplex.substitute_free_doubleton(problem);step=only(result.postsolve_stack)
        @test step.alpha==rhs/pivot && step.beta==-retained/pivot
        @test all(x->denominator(x)>0 && gcd(numerator(x),denominator(x))==1,(step.alpha,step.beta))
        @test result.problem.objective==T[3+2step.beta] && result.problem.objective_constant==7+2step.alpha
        @test JSimplex.postsolve_primal(result,T[2])==T[step.alpha+2step.beta,2]
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower)
    end
end

@testset "Doubleton equal-denominator ratios preserve precision gates" begin
    for sign in (-1,1), mode in (:exact,:alpha,:beta,:zero_rhs), ambient in (32,64,256)
        problem,alpha,beta=setprecision(BigFloat,256) do
            huge=BigInt(1)<<200;pivot=sign*huge
            rhs=mode==:zero_rhs ? BigInt(0) : mode==:alpha ? huge+1 : huge
            retained=mode in (:beta,:zero_rhs) ? huge+1 : huge
            p=LinearProblem(sparse(reshape(BigFloat[pivot,retained],1,2)),BigFloat[0,3];objective_constant=BigFloat(7),
                row_lower=BigFloat[rhs],row_upper=BigFloat[rhs],column_lower=[nothing,BigFloat(-10)],column_upper=[nothing,BigFloat(10)])
            p,rhs//pivot,-retained//pivot
        end
        original=deepcopy(problem)
        setprecision(BigFloat,ambient) do
            result=JSimplex.substitute_free_doubleton(problem);accepted=ambient==256 || mode==:exact
            @test isempty(result.postsolve_stack)==!accepted
            if accepted
                step=only(result.postsolve_stack)
                @test JSimplex._exact_rational(step.alpha)==alpha && JSimplex._exact_rational(step.beta)==beta
            else
                @test result.problem===problem
            end
            @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower)
            @test precision(problem.A[1,1])==256 && precision(bound_value(problem.row_lower[1]))==256
        end
    end
    for T in (Float32,Float64,BigFloat), sign in (-1,1), mode in (:alpha,:beta)
        pivot=T(3sign);rhs=mode==:alpha ? T(1) : pivot;retained=mode==:beta ? T(1) : pivot
        problem=LinearProblem(sparse(reshape(T[pivot,retained],1,2)),T[0,3];row_lower=T[rhs],row_upper=T[rhs],
            column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
        original=deepcopy(problem);result=JSimplex.substitute_free_doubleton(problem)
        @test result.problem===problem && isempty(result.postsolve_stack)
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.row_lower,original.row_lower)
    end
end

@testset "Doubleton equal ratio denominators reduce rejected-candidate allocations" begin
function doubleton_equal_ratio_denominator_probe(kind; count=128, T=Float64)
    fractional=kind in (:fraction_positive,:fraction_negative,:unequal)
    pivot=kind==:unit ? one(T) : fractional ? T(1)/2 : T(2)
    kind in (:negative,:fraction_negative) && (pivot=-pivot)
    rhs=kind in (:fraction_positive,:fraction_negative) ? T(3)/2 : T(4)
    retained=kind in (:fraction_positive,:fraction_negative) ? T(5)/2 : T(3)
    tiny=T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
    rows=collect(1:count)
    A=sparse(vcat(rows,rows),vcat(rows,rows.+count),vcat(fill(pivot,count),fill(retained,count)),count,2count)
    problem=LinearProblem(A,vcat(fill(T(3),count),fill(tiny,count));objective_constant=T(7),
        row_lower=fill(rhs,count),row_upper=fill(rhs,count),
        column_lower=vcat(fill(nothing,count),fill(T(-10),count)),
        column_upper=vcat(fill(nothing,count),fill(T(10),count)))
    return problem,JSimplex.substitute_free_doubleton
end
    for T in (Float32,Float64,BigFloat), kind in (:positive,:negative,:fraction_positive,:fraction_negative,:unequal,:unit)
        problem,pass=doubleton_equal_ratio_denominator_probe(kind;count=4,T);original=deepcopy(problem);result=pass(problem)
        @test result.problem===problem && isempty(result.postsolve_stack)
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective)
        @test isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:positive,:negative,:fraction_positive,:fraction_negative,:unequal,:unit)
        count=4;problem,pass=doubleton_equal_ratio_denominator_probe(kind;count,T);fill!(problem.objective,T(3))
        original=deepcopy(problem);result=pass(problem);step=only(result.postsolve_stack)
        alpha=bound_value(problem.row_lower[1])/problem.A[1,1];beta=-problem.A[1,count+1]/problem.A[1,1]
        @test step.eliminated==1 && step.retained==count+1 && step.equality_row==1
        @test step.alpha==alpha && step.beta==beta
        @test result.problem.A==problem.A[2:count,2:2count]
        expected=fill(T(3),2count-1);expected[count]+=3beta
        @test result.problem.objective==expected && result.problem.objective_constant==7+3alpha
        @test result.problem.row_lower==problem.row_lower[2:count] && result.problem.row_upper==problem.row_upper[2:count]
        primal=ones(T,2count-1);restored=JSimplex.postsolve_primal(result,primal)
        @test restored==[alpha+beta;primal]
        @test problem.objective_constant+sum(problem.objective.*restored)==result.problem.objective_constant+sum(result.problem.objective.*primal)
        m,n=size(result.problem.A);basis=JSimplex.Basis(collect(n+1:n+m),[fill(JSimplex.FREE_NONBASIC,n);fill(JSimplex.BASIC,m)])
        @test JSimplex.restore_basis(result,basis).basic_indices==[1;collect(2count+2:3count)]
        result.problem.objective[1]+=one(T);result.problem.A.nzval[1]+=one(T);result.problem.row_upper[1]=Bound(T(20))
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective)
        @test isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
    for (kind,limit) in ((:positive,23440),(:negative,23440),(:fraction_positive,23440),(:fraction_negative,23440),(:unequal,24004),(:unit,20164))
        problem,pass=doubleton_equal_ratio_denominator_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
