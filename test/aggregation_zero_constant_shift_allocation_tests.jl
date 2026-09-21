using SparseArrays

@testset "Zero constant shifts preserve objectives and projections" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), ratio in (-3,-1,-1//2,1//2,1,3), negative in (false,true), constant in (0,7), implied in (false,true)
        rhs=negative ? -zero(T) : zero(T)
        problem=LinearProblem(sparse(T[2 3;6 5]),T[2ratio,5];objective_constant=constant==0 ? -zero(T) : T(constant),
            row_lower=T[rhs,-100],row_upper=T[rhs,100],
            column_lower=[implied ? nothing : T(1),nothing],column_upper=[implied ? nothing : T(3),nothing])
        original=deepcopy(problem)
        result=JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A)==(implied ? 1 : 2,1)
        @test isequal(result.problem.objective_constant,T(constant))
        @test result.problem.objective==T[5-3ratio]
        @test result.problem.A[end,1]==T(-4)
        @test JSimplex.bound_value(result.problem.row_lower[end])==-100 && JSimplex.bound_value(result.problem.row_upper[end])==100
        x=JSimplex.postsolve_primal(result,T[2])
        @test x==T[-3,2]
        @test sum(problem.objective.*x)+problem.objective_constant==2only(result.problem.objective)+result.problem.objective_constant
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Zero constant shifts preserve previously committed constants" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), ratios in ((1,-1),(-1,3),(3,-3),(3,0)), rhs in ((4,0),(0,-1),(1,-0.0))
        r1,r2=ratios;b1,b2=rhs
        problem=LinearProblem(sparse(T[2 0 3;0 2 3;2 2 5]),T[2r1,2r2,5];objective_constant=T(7),
            row_lower=[T(b1),T(b2),nothing],row_upper=T[b1,b2,20],column_lower=fill(nothing,3),column_upper=fill(nothing,3))
        original=deepcopy(problem)
        result=JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A)==(1,1)
        @test result.problem.objective_constant==T(7+r1*b1+r2*b2)
        @test result.problem.objective==T[5-3r1-3r2]
        @test JSimplex.bound_value(result.problem.row_upper[1])==T(20-b1-b2)
        @test JSimplex.postsolve_primal(result,T[2])==T[(b1-6)/2,(b2-6)/2,2]
        @test isequal(problem.objective_constant,original.objective_constant) && isequal(problem.objective,original.objective) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Unchanged constants still pass BigFloat representation gates" begin
    for mode in (:exact,:tiny,:inexact), ambient in (32,64,256), direction in (-1,1), unit in (false,true)
        problem=setprecision(BigFloat,256) do
            epsilon=BigFloat(2)^(-200)
            ratio=direction*(unit ? BigFloat(1) : BigFloat(3)+epsilon)
            constant=mode==:exact ? BigFloat(7) : mode==:tiny ? epsilon : BigFloat(7)+epsilon
            A=sparse([1,2,1,2],[1,1,2,2],BigFloat[2,0,1,5],2,2)
            LinearProblem(A,BigFloat[2ratio,ratio];objective_constant=constant,
                row_lower=[BigFloat(-0.0),BigFloat(-100)],row_upper=[BigFloat(-0.0),BigFloat(100)],
                column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        saved_constant=JSimplex._exact_rational(problem.objective_constant)
        saved_cost=JSimplex._exact_rational.(problem.objective)
        setprecision(BigFloat,ambient) do
            result=JSimplex.aggregate_sparse_equalities(problem)
            if mode==:inexact && ambient<256
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            else
                @test size(result.problem.A)==(1,1)
                @test JSimplex._exact_rational(result.problem.objective_constant)==saved_constant
                @test precision(result.problem.objective_constant)==ambient
                @test result.problem.objective==BigFloat[0]
                @test precision(JSimplex.bound_value(result.problem.row_upper[1]))==256
            end
            @test JSimplex._exact_rational(problem.objective_constant)==saved_constant
            @test JSimplex._exact_rational.(problem.objective)==saved_cost
            @test precision(problem.objective_constant)==256
        end
    end
end

@testset "Tiny nonzero right-hand sides keep constant contributions" begin
    for constant in (0,7), ambient in (32,64,256), direction in (-1,1)
        problem=setprecision(BigFloat,256) do
            rhs=direction*BigFloat(2)^(-200)
            A=sparse([1,2,1,2],[1,1,2,2],BigFloat[2,0,1,5],2,2)
            LinearProblem(A,BigFloat[6,3];objective_constant=BigFloat(constant),
                row_lower=[rhs,nothing],row_upper=[rhs,nothing],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        expected=constant+3JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[1]))
        setprecision(BigFloat,ambient) do
            result=JSimplex.aggregate_sparse_equalities(problem)
            if constant==7 && ambient<256
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            else
                @test size(result.problem.A)==(1,1)
                @test JSimplex._exact_rational(result.problem.objective_constant)==expected
                @test !iszero(result.problem.objective_constant)
            end
            @test problem.objective_constant==constant
        end
    end
end

@testset "Zero constant shifts preserve non-dyadic rational values" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), direction in (-1,1), unit in (false,true)
        value=T((BigInt(1)<<300)+1,BigInt(den));ratio=unit ? T(direction) : direction*value
        problem=LinearProblem(sparse(T[2 1;2 5]),T[2ratio,ratio];objective_constant=value,
            row_lower=[T(0),nothing],row_upper=[T(0),nothing],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original=deepcopy(problem)
        result=JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A)==(1,1)
        @test result.problem.objective_constant==value
        @test gcd(numerator(result.problem.objective_constant),denominator(result.problem.objective_constant))==1
        @test result.problem.objective==T[0]
        @test JSimplex.postsolve_primal(result,T[2])==T[-1,2]
        @test problem.objective_constant==original.objective_constant && problem.objective==original.objective
    end
end

@testset "Sparse aggregation avoids zero constant shifts" begin
function aggregation_zero_constant_shift_probe(kind; count=128)
    ratio = kind == :unit_positive ? 1.0 : kind == :unit_negative ? -1.0 : kind == :zero_ratio ? 0.0 : kind == :negative ? -3.0 : 3.0
    rhs = kind == :nonzero_rhs ? 4.0 : kind in (:negative,:unit_negative) ? -0.0 : 0.0
    term = 3.0
    odd = collect(1:2:2count); even = odd .+ 1
    A = sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(2.0,count),fill(term,count),fill(6.0,count),fill(5.0,count)),2count,2count)
    problem = LinearProblem(A,[isodd(i) ? 2ratio : 5.0 for i in 1:2count];objective_constant=7.0,
        row_lower=Union{Nothing,Float64}[isodd(i) ? rhs : nothing for i in 1:2count],
        row_upper=[isodd(i) ? rhs : 20.0 for i in 1:2count],
        column_lower=Union{Nothing,Float64}[isodd(i) ? 1.0 : nothing for i in 1:2count],
        column_upper=Union{Nothing,Float64}[isodd(i) ? 3.0 : nothing for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

    for (kind,limit) in ((:positive,45000),(:negative,45000),(:unit_positive,43400),(:unit_negative,43900),(:nonzero_rhs,54300),(:zero_ratio,38700))
        problem,pass=aggregation_zero_constant_shift_probe(kind)
        pass(problem)
        measured=@timed pass(problem)
        @test Base.gc_alloc_count(measured.gcstats)<=limit
        result=pass(problem)
        ratio=problem.objective[1]/2;rhs=JSimplex.bound_value(problem.row_lower[1])
        @test size(result.problem.A)==(256,128)
        @test result.problem.objective_constant==7+128ratio*rhs
        @test result.problem.objective==fill(5-3ratio,128)
        @test JSimplex.postsolve_primal(result,zeros(128))==repeat([rhs/2,0.0],128)
    end
end
