using SparseArrays

@testset "Equal quotient denominators preserve incremental propagation" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), fail in (false,true)
        problem=LinearProblem(sparse(T[3 5 0;0 1 1]),ones(T,3);objective_constant=T(7),
            row_lower=[nothing,T(fail ? 14 : 7)],row_upper=[T(18),nothing],
            column_lower=ones(T,3),column_upper=T[5,5,10])
        original=deepcopy(problem);active=BitVector([true,false]);changed=falses(3)
        result=JSimplex._propagate_row_bounds(problem,active,changed)
        first_changed=T==Rational{BigInt}
        @test active==[true,false]
        if fail
            @test result.status==INFEASIBLE
            @test changed==[first_changed,true,false]
        else
            @test bound_value.(result.problem.column_lower)==T[1,1,4]
            @test bound_value.(result.problem.column_upper)==T[first_changed ? 13//3 : 5,3,10]
            @test changed==[first_changed,true,true]
            @test JSimplex.postsolve_primal(result,T[1,3,4])==T[1,3,4]
        end
        @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper) && isequal(problem.A.nzval,original.A.nzval)
    end
end

@testset "Shared quotient denominators preserve stored precision gates" begin
    for fractional in (false,true), mode in (:exact,:inexact), ambient in (32,64,256), direction in (-1,1), tighten_upper in (false,true)
        problem=setprecision(BigFloat,256) do
            coefficient=fractional ? (BigFloat(2)^200+1)/BigFloat(2)^201 : BigFloat(2)^200
            endpoint=3coefficient
            mode==:inexact && (endpoint+=fractional ? BigFloat(2)^(-200) : one(BigFloat))
            upper_side=(direction>0)==tighten_upper
            LinearProblem(sparse(reshape([direction*coefficient],1,1)),ones(BigFloat,1);
                row_lower=upper_side ? [nothing] : [direction*endpoint],
                row_upper=upper_side ? [direction*endpoint] : [nothing],
                column_lower=BigFloat[1],column_upper=BigFloat[5])
        end
        original=deepcopy(problem)
        saved_coefficient=JSimplex._exact_rational(only(problem.A.nzval))
        expected=big(3)+(mode==:exact ? big(0)//1 : big(1)//big(2)^200)
        setprecision(BigFloat,ambient) do
            changed=falses(1);result=JSimplex._propagate_row_bounds(problem,trues(1),changed)
            rejected=mode==:inexact && (fractional || ambient<256)
            if rejected
                @test result.problem === problem
                @test !any(changed) && isempty(result.postsolve_stack)
            else
                bounds=tighten_upper ? result.problem.column_upper : result.problem.column_lower
                @test JSimplex._exact_rational(only(bound_value.(bounds)))==expected
                @test precision(bound_value(only(bounds)))==ambient
                @test all(changed)
            end
            @test JSimplex._exact_rational(only(problem.A.nzval))==saved_coefficient
            @test precision(only(problem.A.nzval))==256
            @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper)
        end
    end
end

@testset "Large rational quotients retain canonical signs and bounds" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), sign in (-1,1), direction in (-1,1), tighten_upper in (false,true)
        numerator_value=(BigInt(1)<<300)+1
        coefficient=direction*T(numerator_value,BigInt(den))
        endpoint=direction*sign*T(numerator_value+2,BigInt(den))
        expected=sign*T(numerator_value+2,numerator_value)
        upper_side=(direction>0)==tighten_upper
        problem=LinearProblem(sparse(reshape([coefficient],1,1)),ones(T,1);
            row_lower=upper_side ? [nothing] : [endpoint],
            row_upper=upper_side ? [endpoint] : [nothing],column_lower=T[-5],column_upper=T[5])
        original=deepcopy(problem);changed=falses(1)
        result=JSimplex._propagate_row_bounds(problem,trues(1),changed)
        bounds=tighten_upper ? result.problem.column_upper : result.problem.column_lower
        @test bound_value(only(bounds))==expected
        @test denominator(bound_value(only(bounds)))>0
        @test gcd(numerator(bound_value(only(bounds))),denominator(bound_value(only(bounds))))==1
        @test all(changed)
        @test JSimplex.postsolve_primal(result,[expected])==[expected]
        @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper) && isequal(problem.A.nzval,original.A.nzval)
    end
end

@testset "Quotient fast paths retain redundant and infeasible rows" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), endpoint in (7,41)
        problem=LinearProblem(sparse(reshape(T[3,5],1,2)),ones(T,2);
            row_upper=T[endpoint],column_lower=ones(T,2),column_upper=fill(T(5),2))
        original=deepcopy(problem);result=JSimplex.propagate_row_bounds(problem)
        if endpoint==7
            @test result.status==INFEASIBLE
        else
            @test size(result.problem.A)==(0,2)
            @test JSimplex.postsolve_primal(result,T[2,2])==T[2,2]
        end
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.column_upper,original.column_upper)
    end
end

@testset "Propagation avoids general shared-denominator candidate division" begin
function propagation_equal_quotient_denominator_probe(kind; count=128, T=Float64)
    name = string(kind)
    direction = occursin("negative",name) ? -1 : 1
    scale = startswith(name,"fraction") || kind==:unequal_denominator ? T(1)/2 : one(T)
    upper_side = endswith(name,"upper") || kind in (:unequal_denominator,:unit_coefficient)
    endpoint = T(direction>0 ? (upper_side ? 18 : 30) : (upper_side ? -30 : -18))*scale
    kind == :unequal_denominator && (endpoint=T(17)/2)
    kind == :unit_coefficient && (endpoint=T(4))
    coefficients = kind==:unit_coefficient ? ones(T,2) : T[3,5].*scale.*direction
    A = sparse(repeat(collect(1:count),inner=2),collect(1:2count),
        repeat(coefficients,count),count,2count)
    problem = LinearProblem(A,ones(T,2count);objective_constant=T(7),
        row_lower=upper_side ? fill(nothing,count) : fill(endpoint,count),
        row_upper=upper_side ? fill(endpoint,count) : fill(nothing,count),
        column_lower=ones(T,2count),column_upper=fill(T(5),2count))
    return problem,JSimplex.propagate_row_bounds
end

    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:integer_positive_upper,:integer_positive_lower,:integer_negative_upper,:integer_negative_lower,:fraction_positive_upper,:fraction_positive_lower,:fraction_negative_upper,:fraction_negative_lower,:unequal_denominator,:unit_coefficient)
        problem,pass=propagation_equal_quotient_denominator_probe(kind;count=4,T)
        original=deepcopy(problem);changed=falses(8)
        result=JSimplex._propagate_row_bounds(problem,trues(4),changed)
        lower=ones(T,8);upper=fill(T(5),8)
        if kind==:unequal_denominator
            upper=repeat(T[4,T==Rational{BigInt} ? 14//5 : 5],4)
        elseif kind==:unit_coefficient
            upper=fill(T(3),8)
        else
            upper_side=endswith(string(kind),"upper");positive=!occursin("negative",string(kind))
            if positive==upper_side
                upper=repeat(T[T==Rational{BigInt} ? 13//3 : 5,3],4)
            else
                lower=repeat(T[T==Rational{BigInt} ? 5//3 : 1,3],4)
            end
        end
        @test bound_value.(result.problem.column_upper)==upper
        @test bound_value.(result.problem.column_lower)==lower
        @test changed==[lower[i]>bound_value(problem.column_lower[i]) || upper[i]<bound_value(problem.column_upper[i]) for i in 1:8]
        @test result.problem.A==problem.A && result.problem.objective==problem.objective && result.problem.objective_constant==7
        primal=(lower+upper)./2
        @test JSimplex.postsolve_primal(result,primal)==primal
        for state in (JSimplex.AT_LOWER,JSimplex.AT_UPPER)
            basis=JSimplex.Basis(collect(9:12),[fill(state,8);fill(JSimplex.BASIC,4)])
            restored=JSimplex.restore_basis(result,basis)
            @test restored.basic_indices==basis.basic_indices && restored.states==basis.states
        end
        @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper) && isequal(problem.A.nzval,original.A.nzval)
    end
    for (kind,limit) in ((:integer_positive_upper,32600),(:integer_positive_lower,32600),(:integer_negative_upper,32600),(:integer_negative_lower,32350),(:fraction_positive_upper,33600),(:fraction_positive_lower,33600),(:fraction_negative_upper,33600),(:fraction_negative_lower,33350),(:unequal_denominator,35400),(:unit_coefficient,24500))
        problem,pass=propagation_equal_quotient_denominator_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
