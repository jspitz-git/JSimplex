using SparseArrays

@testset "Equal sum denominators preserve incremental propagation" begin
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

@testset "Stored sum precision is preserved under lower ambient precision" begin
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

@testset "Activity sums cancel and restart without changing bounds" begin
    prefixes=([1,-1],[1,1,-2],[1//2,1//2,-1],[1,1//2,-3//2],[0,1,-1,0])
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), prefix in prefixes,
        direction in (-1,1), scale in (1,1//2)
        coefficients=T.([prefix;1]).*T(direction*scale)
        n=length(coefficients)
        endpoint=T(direction*scale*5//2)
        problem=LinearProblem(sparse(reshape(coefficients,1,n)),ones(T,n);objective_constant=T(7),
            row_lower=[min(zero(T),endpoint)],row_upper=[max(zero(T),endpoint)],
            column_lower=ones(T,n),column_upper=[ones(T,n-1);T(3)])
        original=deepcopy(problem);active=trues(1);changed=falses(n)
        result=JSimplex._propagate_row_bounds(problem,active,changed)
        @test size(result.problem.A)==(1,n)
        @test bound_value.(result.problem.column_lower)==ones(T,n)
        @test bound_value.(result.problem.column_upper)==[ones(T,n-1);T(5//2)]
        @test changed==[falses(n-1);true] && active==[true]
        @test result.problem.objective==problem.objective && result.problem.objective_constant==7
        primal=[ones(T,n-1);T(2)]
        @test JSimplex.postsolve_primal(result,primal)==primal
        basis=JSimplex.Basis([n+1],[fill(JSimplex.AT_LOWER,n);JSimplex.BASIC])
        @test JSimplex.restore_basis(result,basis).states==basis.states
        @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper) && isequal(problem.A.nzval,original.A.nzval)
    end
end

@testset "Large exact sums preserve cancellation and canonical bounds" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), direction in (-1,1), repeat_cancel in (false,true)
        value=direction*T((BigInt(1)<<300)+1,BigInt(den))
        prefix=repeat_cancel ? T[value,2value,-3value] : T[value,-value]
        n=length(prefix)+1
        problem=LinearProblem(sparse(reshape([prefix;one(T)],1,n)),ones(T,n);
            row_lower=T[0],row_upper=T[5//2],column_lower=ones(T,n),column_upper=[ones(T,n-1);T(3)])
        original=deepcopy(problem);result=JSimplex.propagate_row_bounds(problem)
        @test bound_value.(result.problem.column_upper)==[ones(T,n-1);T(5//2)]
        @test all(gcd(numerator(bound_value(b)),denominator(bound_value(b)))==1 for b in result.problem.column_upper)
        @test JSimplex.postsolve_primal(result,ones(T,n))==ones(T,n)
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.column_upper,original.column_upper)
    end
end

@testset "Propagation avoids general equal-denominator activity addition" begin
function propagation_equal_sum_denominator_probe(kind; count=128, T=Float64)
    unequal = kind == :unequal_denominator
    cancelled = kind in (:cancel_integer,:cancel_fraction)
    width = unequal ? 2 : 3
    direction = kind in (:integer_negative,:fraction_negative) ? -1 : 1
    scale = kind in (:fraction_positive,:fraction_negative,:cancel_fraction) ? T(1)/2 : one(T)
    coefficients = unequal ? T[1,1//2] : (cancelled ? T[1,-1,1] : T[1,3,5]).*scale.*direction
    rows = repeat(collect(1:count),inner=width)
    A = sparse(rows,collect(1:width*count),repeat(coefficients,count),count,width*count)
    lower = fill(T(direction>0 ? 0 : -33//2)*scale,count)
    upper = fill(T(direction>0 ? 33//2 : 0)*scale,count)
    (unequal || cancelled) && (upper .= T(5)/2*scale)
    high = cancelled ? repeat(T[1,1,3],count) : fill(T(3),width*count)
    problem = LinearProblem(A,ones(T,width*count);objective_constant=T(7),
        row_lower=lower,row_upper=upper,
        column_lower=kind == :unbounded ? fill(nothing,width*count) : ones(T,width*count),
        column_upper=kind == :unbounded ? fill(nothing,width*count) : high)
    return problem,JSimplex.propagate_row_bounds
end

    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:integer_positive,:integer_negative,:fraction_positive,:fraction_negative,:cancel_integer,:cancel_fraction,:unequal_denominator,:unbounded)
        problem,pass=propagation_equal_sum_denominator_probe(kind;count=4,T)
        original=deepcopy(problem);changed=falses(length(problem.objective))
        result=JSimplex._propagate_row_bounds(problem,trues(4),changed)
        if kind==:unbounded
            @test result.problem === problem
            @test !any(changed)
        else
            expected=kind==:unequal_denominator ? repeat(T[2,3],4) :
                kind in (:cancel_integer,:cancel_fraction) ? repeat(T[1,1,5//2],4) : repeat(T[3,3,5//2],4)
            @test bound_value.(result.problem.column_upper)==expected
            @test bound_value.(result.problem.column_lower)==ones(T,length(expected))
            @test changed==[expected[i]<bound_value(problem.column_upper[i]) for i in eachindex(expected)]
        end
        @test result.problem.A==problem.A && result.problem.objective==problem.objective && result.problem.objective_constant==7
        @test JSimplex.postsolve_primal(result,ones(T,length(problem.objective)))==ones(T,length(problem.objective))
        m,n=size(result.problem.A);basis=JSimplex.Basis(collect(n+1:n+m),[fill(JSimplex.FREE_NONBASIC,n);fill(JSimplex.BASIC,m)])
        @test JSimplex.restore_basis(result,basis).basic_indices==basis.basic_indices
        @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper) && isequal(problem.A.nzval,original.A.nzval)
    end
    for (kind,limit) in ((:integer_positive,55100),(:integer_negative,56000),(:fraction_positive,61400),(:fraction_negative,61000),(:cancel_integer,33600),(:cancel_fraction,44700),(:unequal_denominator,34400),(:unbounded,9900))
        problem,pass=propagation_equal_sum_denominator_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
