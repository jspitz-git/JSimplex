using SparseArrays

@testset "Unit constant products preserve objectives and projections" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), ratio in (-3,-1,0,1,3), rhs in (-4,-1,0,1,4), implied in (false,true)
        problem=LinearProblem(sparse(T[2 3;6 5]),T[2ratio,5];objective_constant=T(7),
            row_lower=T[rhs,-100],row_upper=T[rhs,100],
            column_lower=[implied ? nothing : T(1),nothing],column_upper=[implied ? nothing : T(3),nothing])
        original=deepcopy(problem)
        result=JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A)==(implied ? 1 : 2,1)
        @test result.problem.objective_constant==T(7+ratio*rhs)
        @test result.problem.objective==T[5-3ratio]
        @test result.problem.A[end,1]==T(-4)
        @test JSimplex.bound_value(result.problem.row_lower[end])==-100-3rhs && JSimplex.bound_value(result.problem.row_upper[end])==100-3rhs
        x=JSimplex.postsolve_primal(result,T[2])
        @test x==T[(rhs-6)/2,2]
        @test sum(problem.objective.*x)+problem.objective_constant==2only(result.problem.objective)+result.problem.objective_constant
        @test isequal(problem.A.nzval,original.A.nzval) && isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant) && isequal(problem.row_lower,original.row_lower) && isequal(problem.row_upper,original.row_upper)
    end
end

@testset "Unit constant products accumulate committed shifts" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), ratios in ((1,-1),(-1,3),(3,-3),(0,1)), rhs in ((4,-1),(1,-1))
        r1,r2=ratios; b1,b2=rhs
        problem=LinearProblem(sparse(T[2 0 3;0 2 3;2 2 5]),T[2r1,2r2,5];objective_constant=T(7),
            row_lower=[T(b1),T(b2),nothing],row_upper=T[b1,b2,20],
            column_lower=fill(nothing,3),column_upper=fill(nothing,3))
        original=deepcopy(problem)
        result=JSimplex.aggregate_sparse_equalities(problem)
        @test size(result.problem.A)==(1,1)
        @test result.problem.objective_constant==T(7+r1*b1+r2*b2)
        @test result.problem.objective==T[5-3r1-3r2]
        @test JSimplex.bound_value(result.problem.row_upper[1])==T(20-b1-b2)
        @test JSimplex.postsolve_primal(result,T[2])==T[(b1-6)/2,(b2-6)/2,2]
        @test isequal(problem.objective,original.objective) && isequal(problem.objective_constant,original.objective_constant) && isequal(problem.A.nzval,original.A.nzval)
    end
end

@testset "Constant products distinguish stored high-precision unit neighbors" begin
    for side in (:ratio,:rhs), mode in (:exact,:near,:tail,:cancel), ambient in (32,64,256), direction in (-1,1)
        problem=setprecision(BigFloat,256) do
            epsilon=BigFloat(2)^(-200)
            unit=direction*(BigFloat(1)+(mode == :exact ? zero(BigFloat) : epsilon))
            ratio,rhs=side == :ratio ? (unit,BigFloat(3)) : (BigFloat(3),unit)
            constant=mode == :tail ? BigFloat(-3direction) : mode == :cancel ? -ratio*rhs : BigFloat(7)
            # Stored zero keeps pivot degree two without shifting affected rows.
            A=sparse([1,2,1,2],[1,1,2,2],BigFloat[2,0,1,5],2,2)
            LinearProblem(A,BigFloat[2ratio,ratio];objective_constant=constant,
                row_lower=[rhs,nothing],row_upper=[rhs,nothing],
                column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        end
        saved_cost=JSimplex._exact_rational.(problem.objective)
        saved_constant=JSimplex._exact_rational(problem.objective_constant)
        saved_rhs=JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[1]))
        expected=saved_constant+saved_cost[1]/2*saved_rhs
        setprecision(BigFloat,ambient) do
            result=JSimplex.aggregate_sparse_equalities(problem)
            if mode == :near && ambient < 256
                @test result.problem === problem
                @test isempty(result.postsolve_stack)
            else
                @test size(result.problem.A)==(1,1)
                @test JSimplex._exact_rational(result.problem.objective_constant)==expected
                @test precision(result.problem.objective_constant)==ambient
                @test result.problem.objective==BigFloat[0]
            end
            @test JSimplex._exact_rational.(problem.objective)==saved_cost
            @test JSimplex._exact_rational(problem.objective_constant)==saved_constant
            @test JSimplex._exact_rational(JSimplex.bound_value(problem.row_lower[1]))==saved_rhs
        end
    end
end

@testset "Unit constant products preserve non-dyadic rational values" begin
    T=Rational{BigInt}
    for den in (5,7,15,21), direction in (-1,1), side in (:ratio,:rhs)
        value=T((BigInt(1)<<300)+1,BigInt(den))
        ratio,rhs=side == :ratio ? (T(direction),value) : (value,T(direction))
        A=sparse([1,2,1,2],[1,1,2,2],T[2,0,1,5],2,2)
        problem=LinearProblem(A,T[2ratio,ratio];objective_constant=T(7),
            row_lower=[rhs,nothing],row_upper=[rhs,nothing],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original=deepcopy(problem)
        result=JSimplex.aggregate_sparse_equalities(problem)
        expected=7+ratio*rhs
        @test size(result.problem.A)==(1,1)
        @test result.problem.objective_constant==expected
        @test gcd(numerator(result.problem.objective_constant),denominator(result.problem.objective_constant))==1
        @test result.problem.objective==T[0]
        @test JSimplex.postsolve_primal(result,T[0])==T[rhs/2,0]
        @test problem.objective_constant==original.objective_constant && problem.objective==original.objective && problem.row_lower==original.row_lower
    end
end

@testset "Unit constant products retain rejection and signed-zero behavior" begin
    for T in (Float32,Float64), direction in (-1,1), mode in (:overflow,:half_subnormal)
        cost=mode == :overflow ? T(1) : T(direction)*nextfloat(zero(T))
        rhs=mode == :overflow ? T(direction)*floatmax(T) : T(1)
        constant=mode == :overflow ? rhs : zero(T)
        A=sparse([1,2,1,2],[1,1,2,2],T[mode == :overflow ? 1 : 2,0,3,5],2,2)
        problem=LinearProblem(A,T[cost,0];objective_constant=constant,row_lower=[rhs,nothing],row_upper=[rhs,nothing],
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        original=deepcopy(problem)
        result=JSimplex.aggregate_sparse_equalities(problem)
        @test isempty(result.postsolve_stack) || all(record.column != 1 for record in only(result.postsolve_stack).records)
        @test isfinite(result.problem.objective_constant)
        @test isequal(problem.objective_constant,original.objective_constant) && isequal(problem.objective,original.objective) && isequal(problem.A.nzval,original.A.nzval)
    end
    for T in (Float32,Float64,BigFloat), ratio in (-1,1), negative in (false,true)
        rhs=negative ? -zero(T) : zero(T)
        problem=LinearProblem(sparse(T[2 3;6 5]),T[2ratio,5];objective_constant=-zero(T),
            row_lower=[rhs,nothing],row_upper=[rhs,nothing],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        result=JSimplex.aggregate_sparse_equalities(problem)
        @test iszero(result.problem.objective_constant) && !signbit(result.problem.objective_constant)
        @test signbit(problem.objective_constant) && signbit(JSimplex.bound_value(problem.row_lower[1]))==negative
    end
end

@testset "Sparse aggregation avoids unit constant-product multiplication" begin
function aggregation_unit_constant_product_probe(kind; count=128)
    ratio = kind == :ratio_positive ? 1.0 : kind == :ratio_negative ? -1.0 : kind == :zero_ratio ? 0.0 : 3.0
    rhs = kind == :rhs_positive ? 1.0 : kind == :rhs_negative ? -1.0 : 4.0
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

    for (kind,limit) in ((:ratio_positive,52300),(:ratio_negative,52600),(:rhs_positive,52300),(:rhs_negative,52600),(:nonunit,54300),(:zero_ratio,46600))
        problem,pass=aggregation_unit_constant_product_probe(kind)
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
