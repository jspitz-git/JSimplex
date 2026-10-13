using SparseArrays

@testset "Equal candidate denominators preserve incremental propagation" begin
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

@testset "Shared candidate denominators preserve stored precision gates" begin
    for mode in (:exact,:inexact), ambient in (32,64,256), direction in (-1,1), tighten_upper in (false,true)
        problem=setprecision(BigFloat,256) do
            epsilon=BigFloat(2)^(-200)
            endpoint=BigFloat(tighten_upper ? 5 : 7)+(mode==:exact ? epsilon : 3epsilon)
            upper_side=(direction>0)==tighten_upper
            LinearProblem(sparse(reshape(fill(BigFloat(direction),2),1,2)),ones(BigFloat,2);
                row_lower=upper_side ? [nothing] : [direction*endpoint],
                row_upper=upper_side ? [direction*endpoint] : [nothing],
                column_lower=fill(BigFloat(1)+epsilon,2),column_upper=fill(BigFloat(5)+epsilon,2))
        end
        saved_lower=JSimplex._exact_rational.(bound_value.(problem.column_lower))
        saved_upper=JSimplex._exact_rational.(bound_value.(problem.column_upper))
        expected=big(tighten_upper ? 4 : 2)+(mode==:exact ? big(0)//1 : big(2)//big(2)^200)
        setprecision(BigFloat,ambient) do
            changed=falses(2);result=JSimplex._propagate_row_bounds(problem,trues(1),changed)
            if mode==:inexact && ambient<256
                @test result.problem === problem
                @test !any(changed) && isempty(result.postsolve_stack)
            else
                bounds=tighten_upper ? result.problem.column_upper : result.problem.column_lower
                @test JSimplex._exact_rational.(bound_value.(bounds))==fill(expected,2)
                @test all(precision(bound_value(b))==ambient for b in bounds)
                @test all(changed)
            end
            @test JSimplex._exact_rational.(bound_value.(problem.column_lower))==saved_lower
            @test JSimplex._exact_rational.(bound_value.(problem.column_upper))==saved_upper
            @test all(precision(bound_value(b))==256 for b in problem.column_lower)
        end
    end
end

@testset "Large rational candidate differences remain canonical" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), sign in (-1,1), direction in (-1,1), tighten_upper in (false,true)
        value=sign*T((BigInt(1)<<300)+1,BigInt(den))
        endpoint=2value+(tighten_upper ? 3 : 17)
        upper_side=(direction>0)==tighten_upper
        problem=LinearProblem(sparse(reshape(fill(T(direction),2),1,2)),ones(T,2);
            row_lower=upper_side ? [nothing] : [direction*endpoint],
            row_upper=upper_side ? [direction*endpoint] : [nothing],
            column_lower=fill(value,2),column_upper=fill(value+10,2))
        original=deepcopy(problem);changed=falses(2)
        result=JSimplex._propagate_row_bounds(problem,trues(1),changed)
        bounds=tighten_upper ? result.problem.column_upper : result.problem.column_lower
        @test bound_value.(bounds)==fill(value+(tighten_upper ? 3 : 7),2)
        @test all(gcd(numerator(bound_value(b)),denominator(bound_value(b)))==1 for b in bounds)
        @test all(changed)
        @test JSimplex.postsolve_primal(result,fill(value+(tighten_upper ? 2 : 8),2))==fill(value+(tighten_upper ? 2 : 8),2)
        @test isequal(problem.column_lower,original.column_lower) && isequal(problem.column_upper,original.column_upper) && isequal(problem.A.nzval,original.A.nzval)
    end
end

@testset "Propagation avoids general shared-denominator candidate subtraction" begin
function propagation_equal_candidate_denominator_probe(kind; count=128, T=Float64)
    name = string(kind)
    direction = occursin("negative",name) ? -1 : 1
    scale = startswith(name,"fraction") ? T(1)/2 : one(T)
    upper_side = endswith(name,"upper") || kind in (:unequal_denominator,:zero_endpoint)
    endpoint = T(direction>0 ? (upper_side ? 13 : 11) : (upper_side ? -11 : -13))*scale
    kind == :unequal_denominator && (endpoint=T(23)/2)
    kind == :zero_endpoint && (endpoint=zero(T))
    A = sparse(repeat(collect(1:count),inner=2),collect(1:2count),
        repeat(T[1,3].*scale.*direction,count),count,2count)
    problem = LinearProblem(A,ones(T,2count);objective_constant=T(7),
        row_lower=upper_side ? fill(nothing,count) : fill(endpoint,count),
        row_upper=upper_side ? fill(endpoint,count) : fill(nothing,count),
        column_lower=fill(T(kind==:zero_endpoint ? -1 : 1),2count),
        column_upper=fill(T(5),2count))
    return problem,JSimplex.propagate_row_bounds
end

    for T in (Float32,Float64,BigFloat,Rational{BigInt}), kind in (:integer_positive_upper,:integer_positive_lower,:integer_negative_upper,:integer_negative_lower,:fraction_positive_upper,:fraction_positive_lower,:fraction_negative_upper,:fraction_negative_lower,:unequal_denominator,:zero_endpoint)
        problem,pass=propagation_equal_candidate_denominator_probe(kind;count=4,T)
        original=deepcopy(problem);changed=falses(8)
        result=JSimplex._propagate_row_bounds(problem,trues(4),changed)
        lower=fill(T(kind==:zero_endpoint ? -1 : 1),8);upper=fill(T(5),8)
        if kind==:unequal_denominator
            upper=repeat(T[5,7//2],4)
        elseif kind==:zero_endpoint
            upper=repeat(T[3,T==Rational{BigInt} ? 1//3 : 5],4)
        else
            upper_side=endswith(string(kind),"upper");positive=!occursin("negative",string(kind))
            if positive==upper_side
                upper=repeat(T[5,4],4)
            else
                lower=repeat(T[1,2],4)
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
    for (kind,limit) in ((:integer_positive_upper,26200),(:integer_positive_lower,26200),(:integer_negative_upper,27200),(:integer_negative_lower,27000),(:fraction_positive_upper,31830),(:fraction_positive_lower,31830),(:fraction_negative_upper,31830),(:fraction_negative_lower,31570),(:unequal_denominator,31300),(:zero_endpoint,26800))
        problem,pass=propagation_equal_candidate_denominator_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
    end
end
