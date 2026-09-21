using SparseArrays

@testset "Shared fixed sums preserve incremental propagation" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), fail in (false,true)
        problem=LinearProblem(sparse(T[3 5 1 0;0 0 1 1]),ones(T,4);objective_constant=T(7),
            row_lower=[nothing,T(fail ? 14 : 7)],row_upper=[T(11),nothing],
            column_lower=ones(T,4),column_upper=T[1,1,5,10])
        original=deepcopy(problem);active=BitVector([true,false]);changed=falses(4)
        result=JSimplex._propagate_row_bounds(problem,active,changed)
        @test active==[true,false]
        if fail
            @test result.status==INFEASIBLE
            @test changed==[false,false,true,false]
        else
            @test bound_value.(result.problem.column_lower)==T[1,1,1,4]
            @test bound_value.(result.problem.column_upper)==T[1,1,3,10]
            @test changed==[false,false,true,true]
            @test JSimplex.postsolve_primal(result,T[1,1,3,4])==T[1,1,3,4]
        end
        @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper) && isequal(problem.A.nzval,original.A.nzval)
    end
end

@testset "Fixed terms cannot merge previously distinct activity sums" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), direction in (-1,1)
        # After the second contribution, the new minimum equals the OLD maximum.
        # The maximum must still add its fixed contribution, yielding three.
        problem=LinearProblem(sparse(reshape(fill(T(direction),3),1,3)),ones(T,3);
            row_lower=direction>0 ? T[6] : [nothing],
            row_upper=direction>0 ? [nothing] : T[-6],
            column_lower=ones(T,3),column_upper=T[2,1,5])
        original=deepcopy(problem);changed=falses(3)
        result=JSimplex._propagate_row_bounds(problem,trues(1),changed)
        @test bound_value.(result.problem.column_lower)==T[1,1,3]
        @test bound_value.(result.problem.column_upper)==T[2,1,5]
        @test changed==[false,false,true]
        @test problem.column_lower==original.column_lower && problem.column_upper==original.column_upper
    end
end

@testset "Shared fixed sums preserve stored precision and cancellation" begin
    for cancelled in (false,true), mode in (:exact,:inexact), ambient in (32,64,256), direction in (-1,1)
        problem=setprecision(BigFloat,256) do
            epsilon=BigFloat(2)^(-200)
            endpoint=cancelled ? BigFloat(3) : BigFloat(7)+4epsilon
            mode==:inexact && (endpoint+=2epsilon)
            coefficients=(cancelled ? BigFloat[1,-1,1] : BigFloat[1,3,1]).*direction
            LinearProblem(sparse(reshape(coefficients,1,3)),ones(BigFloat,3);
                row_lower=direction>0 ? [nothing] : [-endpoint],
                row_upper=direction>0 ? [endpoint] : [nothing],
                column_lower=[BigFloat(1)+epsilon,BigFloat(1)+epsilon,BigFloat(1)],
                column_upper=[BigFloat(1)+epsilon,BigFloat(1)+epsilon,BigFloat(5)])
        end
        saved_lower=JSimplex._exact_rational.(bound_value.(problem.column_lower))
        saved_upper=JSimplex._exact_rational.(bound_value.(problem.column_upper))
        expected=big(3)+(mode==:exact ? big(0)//1 : big(2)//big(2)^200)
        setprecision(BigFloat,ambient) do
            changed=falses(3);result=JSimplex._propagate_row_bounds(problem,trues(1),changed)
            if mode==:inexact && ambient<256
                @test result.problem === problem
                @test !any(changed) && isempty(result.postsolve_stack)
            else
                @test JSimplex._exact_rational(bound_value(result.problem.column_upper[3]))==expected
                @test precision(bound_value(result.problem.column_upper[3]))==ambient
                @test changed==[false,false,true]
            end
            @test JSimplex._exact_rational.(bound_value.(problem.column_lower))==saved_lower
            @test JSimplex._exact_rational.(bound_value.(problem.column_upper))==saved_upper
            @test all(precision(bound_value(b))==256 for b in problem.column_upper)
        end
    end
end

@testset "Large fixed sums preserve cancellation and source ownership" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), direction in (-1,1), cancelled in (false,true)
        value=direction*T((BigInt(1)<<300)+1,BigInt(den))
        prefix=cancelled ? T[value,-value,2value,-2value] : T[value,2value]
        endpoint=sum(prefix)+3;n=length(prefix)+1
        problem=LinearProblem(sparse(reshape([prefix;one(T)],1,n)),ones(T,n);
            row_upper=[endpoint],column_lower=ones(T,n),column_upper=[ones(T,n-1);T(5)])
        original=deepcopy(problem);changed=falses(n)
        result=JSimplex._propagate_row_bounds(problem,trues(1),changed)
        @test bound_value.(result.problem.column_upper)==[ones(T,n-1);T(3)]
        @test all(gcd(numerator(bound_value(b)),denominator(bound_value(b)))==1 for b in result.problem.column_upper)
        @test changed==[falses(n-1);true]
        @test JSimplex.postsolve_primal(result,ones(T,n))==ones(T,n)
        @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper) && isequal(problem.A.nzval,original.A.nzval)
    end
end

@testset "Shared sums retain exact infeasibility for fixed rows" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), direction in (-1,1)
        problem=LinearProblem(sparse(reshape(T[1,3,5].*direction,1,3)),ones(T,3);
            row_lower=direction>0 ? [nothing] : T[-8],
            row_upper=direction>0 ? T[8] : [nothing],column_lower=ones(T,3),column_upper=ones(T,3))
        original=deepcopy(problem);changed=falses(3)
        result=JSimplex._propagate_row_bounds(problem,trues(1),changed)
        @test result.status==INFEASIBLE
        @test !any(changed)
        @test problem.column_lower==original.column_lower && problem.column_upper==original.column_upper
    end
end

@testset "Propagation reuses matching minimum activity sums" begin
function propagation_shared_fixed_sums_probe(kind; count=128, T=Float64)
    name = string(kind)
    scale = endswith(name,"fraction") ? T(1)/2 : one(T)
    fixed = startswith(name,"fixed")
    cancelled = startswith(name,"cancelled")
    coefficients = (cancelled ? T[1,-1,1] : T[1,3,5]).*scale
    A = sparse(repeat(collect(1:count),inner=3),collect(1:3count),
        repeat(coefficients,count),count,3count)
    high = fixed ? ones(T,3count) : kind==:nonfixed ? fill(T(3),3count) : repeat(T[1,1,3],count)
    endpoint = T(fixed ? 10 : cancelled ? 5//2 : 33//2)*scale
    problem = LinearProblem(A,ones(T,3count);objective_constant=T(7),
        row_lower=zeros(T,count),row_upper=fill(endpoint,count),
        column_lower=kind==:unbounded ? fill(nothing,3count) : ones(T,3count),
        column_upper=kind==:unbounded ? fill(nothing,3count) : high)
    return problem,JSimplex.propagate_row_bounds
end

    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:fixed_integer,:fixed_fraction,:prefix_integer,:prefix_fraction,:cancelled_integer,:cancelled_fraction,:nonfixed,:unbounded)
        problem,pass=propagation_shared_fixed_sums_probe(kind;count=4,T)
        original=deepcopy(problem);changed=falses(12)
        result=JSimplex._propagate_row_bounds(problem,trues(4),changed)
        fixed=startswith(string(kind),"fixed")
        if kind==:unbounded
            @test result.problem === problem
            @test !any(changed)
        elseif fixed
            @test size(result.problem.A)==(0,12)
            @test bound_value.(result.problem.column_upper)==ones(T,12)
            @test !any(changed)
        else
            expected=repeat(kind==:nonfixed ? T[3,3,5//2] : T[1,1,5//2],4)
            @test bound_value.(result.problem.column_upper)==expected
            @test changed==repeat([false,false,true],4)
            @test result.problem.A==problem.A
        end
        @test result.problem.column_lower==problem.column_lower
        @test result.problem.objective==problem.objective && result.problem.objective_constant==7
        @test JSimplex.postsolve_primal(result,ones(T,12))==ones(T,12)
        m,n=size(result.problem.A)
        for state in (JSimplex.AT_LOWER,JSimplex.AT_UPPER)
            basis=JSimplex.Basis(collect(n+1:n+m),[fill(state,n);fill(JSimplex.BASIC,m)])
            restored=JSimplex.restore_basis(result,basis)
            @test restored.basic_indices==collect(13:16) && restored.states==[fill(state,12);fill(JSimplex.BASIC,4)]
        end
        @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper) && isequal(problem.A.nzval,original.A.nzval)
    end
    for (kind,limit) in ((:fixed_integer,19550),(:fixed_fraction,24150),(:prefix_integer,50150),(:prefix_fraction,56550),(:cancelled_integer,32100),(:cancelled_fraction,43350),(:nonfixed,53850),(:unbounded,9900))
        problem,pass=propagation_shared_fixed_sums_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
