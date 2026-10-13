using SparseArrays

@testset "Other activity preserves exact values and earlier shortcuts" begin
    T=Rational{BigInt}
    cases=((9,3),(-9,-3),(9//2,1//2),(9//2,3//2),(-9//2,-3//2),(2,1//2),(7//5,2//5),(7//5,-2//5),(0,2//3),(2//3,0),(2//3,2//3))
    for (a,b) in cases, unbounded in (0,1,2), shared in (false,true)
        total,term=T(a),T(b);seed=shared ? zero(T) : nothing
        saved_total,saved_term=deepcopy(total),deepcopy(term)
        result=JSimplex._other_activity(total,unbounded,term,seed)
        @test result==(unbounded==0 ? total-term : nothing)
        @test total==saved_total && term==saved_term
        @test isnothing(seed) || iszero(seed)
        if unbounded==0
            @test gcd(numerator(result),denominator(result))==1
            total==term && shared && (@test result===seed)
            iszero(term) && (@test result===total)
        end
    end
    for unbounded in (0,1,2), shared in (false,true)
        total=T(7,5);seed=shared ? zero(T) : nothing
        result=JSimplex._other_activity(total,unbounded,nothing,seed)
        @test result==(unbounded==1 ? total : nothing)
        unbounded==1 && (@test result===total)
    end
    for den in (5,7,15,21), direction in (-1,1), factor in (-2,-1,1,2,4)
        term=direction*T((BigInt(1)<<300)+1,BigInt(den));total=factor*term
        original=deepcopy((total,term))
        expected=total-term;result=JSimplex._other_activity(total,0,term)
        @test result==expected && denominator(result)==denominator(expected)
        @test gcd(numerator(result),denominator(result))==1
        @test (total,term)==original
    end
end

@testset "Equal activity denominators preserve incremental propagation" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), fail in (false,true)
        problem=LinearProblem(sparse(T[1 3 5 0;0 0 1 1]),ones(T,4);objective_constant=T(7),
            row_lower=T[0,fail ? 13 : 6],row_upper=[T(33//2),nothing],
            column_lower=ones(T,4),column_upper=T[3,3,3,10])
        original=deepcopy(problem);active=BitVector([true,false]);changed=falses(4)
        result=JSimplex._propagate_row_bounds(problem,active,changed)
        @test active==[true,false]
        if fail
            @test result.status==INFEASIBLE
            @test changed==[false,false,true,false]
        else
            @test JSimplex.bound_value.(result.problem.column_lower)==T[1,1,1,7//2]
            @test JSimplex.bound_value.(result.problem.column_upper)==T[3,3,5//2,10]
            @test changed==[false,false,true,true]
            @test JSimplex.postsolve_primal(result,T[1,1,2,4])==T[1,1,2,4]
        end
        @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper) && isequal(problem.A.nzval,original.A.nzval)
    end
end

@testset "Stored activity precision is preserved under lower ambient precision" begin
    for mode in (:exact,:inexact), ambient in (32,64,256), direction in (-1,1)
        problem=setprecision(BigFloat,256) do
            epsilon=mode==:exact ? zero(BigFloat) : BigFloat(2)^(-200)
            endpoint=mode==:exact ? BigFloat(9)/2 : BigFloat(5)
            LinearProblem(sparse(reshape(fill(BigFloat(direction),3),1,3)),ones(BigFloat,3);
                row_lower=[direction>0 ? BigFloat(0) : -endpoint],row_upper=[direction>0 ? endpoint : BigFloat(0)],
                column_lower=fill(BigFloat(1)+epsilon,3),column_upper=fill(BigFloat(3)+epsilon,3))
        end
        saved_lower=JSimplex._exact_rational.(JSimplex.bound_value.(problem.column_lower))
        saved_upper=JSimplex._exact_rational.(JSimplex.bound_value.(problem.column_upper))
        expected=mode==:exact ? big(5)//2 : big(3)-big(2)//big(2)^200
        setprecision(BigFloat,ambient) do
            result=JSimplex.propagate_row_bounds(problem)
            if mode==:inexact && ambient<256
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            else
                @test JSimplex._exact_rational.(JSimplex.bound_value.(result.problem.column_upper))==fill(expected,3)
                @test all(precision(JSimplex.bound_value(b))==ambient for b in result.problem.column_upper)
                @test size(result.problem.A)==(1,3)
            end
            @test JSimplex._exact_rational.(JSimplex.bound_value.(problem.column_lower))==saved_lower
            @test JSimplex._exact_rational.(JSimplex.bound_value.(problem.column_upper))==saved_upper
            @test all(precision(JSimplex.bound_value(b))==256 for b in problem.column_upper)
        end
    end
end

@testset "Propagation row removal and infeasibility remain exact" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), endpoint in (8,30)
        problem=LinearProblem(sparse(reshape(T[1,3,5],1,3)),ones(T,3);
            row_lower=T[0],row_upper=T[endpoint],column_lower=ones(T,3),column_upper=fill(T(3),3))
        original=deepcopy(problem);result=JSimplex.propagate_row_bounds(problem)
        if endpoint==8
            @test result.status==INFEASIBLE
        else
            @test size(result.problem.A)==(0,3)
            @test JSimplex.postsolve_primal(result,T[2,2,2])==T[2,2,2]
        end
        @test problem.column_lower==original.column_lower && problem.column_upper==original.column_upper && problem.A==original.A
    end
end

@testset "Propagation avoids general equal-denominator activity subtraction" begin
function propagation_equal_activity_denominator_probe(kind; count=128, T=Float64)
    unequal = kind == :unequal_denominator
    width = unequal ? 2 : 3
    direction = kind in (:integer_negative,:fraction_negative) ? -1 : 1
    scale = kind in (:fraction_positive,:fraction_negative,:unequal_denominator) ? T(1)/2 : one(T)
    coefficients = unequal ? T[1,3].*scale : T[1,3,5].*scale.*direction
    rows = repeat(collect(1:count),inner=width)
    A = sparse(rows,collect(1:width*count),repeat(coefficients,count),count,width*count)
    lower = fill(T(direction>0 ? 0 : -33//2)*scale,count)
    upper = fill(T(direction>0 ? 33//2 : 0)*scale,count)
    unequal && (upper .= T(5)/2)
    problem = LinearProblem(A,ones(T,width*count);objective_constant=T(7),
        row_lower=lower,row_upper=upper,
        column_lower=kind == :unbounded ? fill(nothing,width*count) : ones(T,width*count),
        column_upper=kind == :unbounded ? fill(nothing,width*count) : fill(T(3),width*count))
    return problem,JSimplex.propagate_row_bounds
end

    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:integer_positive,:integer_negative,:fraction_positive,:fraction_negative,:unequal_denominator,:unbounded)
        problem,pass=propagation_equal_activity_denominator_probe(kind;count=4,T)
        original=deepcopy(problem);changed=falses(length(problem.objective))
        result=JSimplex._propagate_row_bounds(problem,trues(4),changed)
        if kind==:unbounded
            @test result.problem === problem
            @test !any(changed)
        else
            expected=kind==:unequal_denominator ? repeat(T[2,T==Rational{BigInt} ? 4//3 : 3],4) : repeat(T[3,3,5//2],4)
            @test JSimplex.bound_value.(result.problem.column_upper)==expected
            @test JSimplex.bound_value.(result.problem.column_lower)==ones(T,length(expected))
            @test changed==[expected[i]<3 for i in eachindex(expected)]
        end
        @test result.problem.A==problem.A && result.problem.objective==problem.objective && result.problem.objective_constant==7
        @test JSimplex.postsolve_primal(result,ones(T,length(problem.objective)))==ones(T,length(problem.objective))
        m,n=size(result.problem.A);basis=JSimplex.Basis(collect(n+1:n+m),[fill(JSimplex.FREE_NONBASIC,n);fill(JSimplex.BASIC,m)])
        @test JSimplex.restore_basis(result,basis).basic_indices==basis.basic_indices
        @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper) && isequal(problem.A.nzval,original.A.nzval)
    end
    for (kind,limit) in ((:integer_positive,56500),(:integer_negative,57400),(:fraction_positive,61900),(:fraction_negative,61500),(:unequal_denominator,41600),(:unbounded,9900))
        problem,pass=propagation_equal_activity_denominator_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
