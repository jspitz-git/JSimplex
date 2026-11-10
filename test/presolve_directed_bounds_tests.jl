using SparseArrays

@testset "Directed bounds preserve stored-cache implications" begin
    for T in (Float32, Float64)
        Q = Rational{BigInt}
        p = LinearProblem(sparse(T[3 0; 3 1]), zeros(T, 2);
            row_lower=[nothing, T(1)], row_upper=[T(1), nothing],
            column_lower=T[0, -1])
        before = deepcopy(p)
        r = JSimplex.propagate_row_bounds(p)
        @test isfinite(r.problem.column_upper[1])
        if isfinite(r.problem.column_upper[1])
            hi = bound_value(r.problem.column_upper[1])
            lo = bound_value(r.problem.column_lower[2])
            @test Q(hi) > Q(1, 3)
            @test Q(lo) <= 1 - 3Q(hi) < 0
            @test Q(nextfloat(lo)) > 1 - 3Q(hi)
        end
        @test p.A == before.A && p.column_lower == before.column_lower && p.column_upper == before.column_upper
        p = LinearProblem(sparse(reshape(T[3, -1], 1, 2)), zeros(T, 2);
            row_lower=T[1], column_lower=[nothing, T(0)])
        r = JSimplex.propagate_row_bounds(p)
        @test isfinite(r.problem.column_lower[1])
        if isfinite(r.problem.column_lower[1])
            lo = bound_value(r.problem.column_lower[1])
            @test Q(lo) <= Q(1, 3) < Q(nextfloat(lo))
        end
    end
end

@testset "Directed endpoint conversion encloses exact rational results" begin
    Q = Rational{BigInt}
    for T in (Float32, Float64)
        values = (Q(1,3), Q(-1,3), Q(1,10), Q(-1,10), Q(0), Q(1), Q(-1), Q(2)^53+1,
                  Q(nextfloat(zero(T)))/2, -Q(nextfloat(zero(T)))/2)
        for q in values, upper in (false, true)
            r = JSimplex._propagation_bound(T, q, upper, true)
            @test !isnothing(r)
            if !isnothing(r)
                value, stored = r
                @test stored == Q(value)
                @test upper ? stored >= q : stored <= q
                @test stored == q || (upper ? Q(prevfloat(value)) < q : Q(nextfloat(value)) > q)
                @test stored != q || stored === q # Exact conversions reuse the owned rational.
            end
        end
        @test isnothing(JSimplex._propagation_bound(T, 2Q(floatmax(T)), true, true))
        @test isnothing(JSimplex._propagation_bound(T, -2Q(floatmax(T)), false, true))
        @test isnothing(JSimplex._propagation_bound(T, Q(1,3), true, false))
        q = Q(3,2)
        @test JSimplex._propagation_bound(T, q, true, false)[2] === q
    end
end

@testset "Strict modes and rational types retain exact propagation" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        p = LinearProblem(sparse(reshape(T[3,1],1,2)), zeros(T,2);
            row_upper=T[1], column_lower=T[0,0])
        strict = JSimplex.propagate_row_bounds(p; directed_bounds=false)
        if T <: Rational
            @test bound_value(strict.problem.column_upper[1]) == T(1//3)
        else
            @test !isfinite(strict.problem.column_upper[1])
        end
        if T === BigFloat
            hi=bound_value(JSimplex.propagate_row_bounds(p).problem.column_upper[1])
            @test Rational{BigInt}(prevfloat(hi))<1//3<=Rational{BigInt}(hi)
        end
        # Zero tolerance must carry strict mode through the entire dispatcher.
        a = JSimplex._presolve_for_solve(p, zero(T))
        b = JSimplex.presolve_problem(p; directed_bounds=false)
        @test a.problem.A == b.problem.A && a.problem.column_upper == b.problem.column_upper
        @test a.problem.column_lower == b.problem.column_lower
    end
    old = get_zero_subnormals()
    try
        set_zero_subnormals(true)
        for T in (Float32,Float64)
            p=LinearProblem(sparse(reshape(T[3,1],1,2)),zeros(T,2);row_upper=T[1],column_lower=T[0,0])
            @test !isfinite(JSimplex.propagate_row_bounds(p).problem.column_upper[1])
        end
    finally
        set_zero_subnormals(old)
    end
end

@testset "Directed propagation follows changed rows and negative coefficients" begin
    Q=Rational{BigInt}
    for T in (Float32,Float64), sign in (-1,1)
        p=LinearProblem(sparse(T[3 0;sign*3 sign]),zeros(T,2);
            row_upper=sign==1 ? [T(1),nothing] : T[1,-1],
            row_lower=sign==1 ? [nothing,T(1)] : [nothing,nothing],column_lower=T[0,-1])
        changed=falses(2)
        r=JSimplex._propagate_row_bounds(p,BitVector([true,false]),changed)
        hi=bound_value(r.problem.column_upper[1]);lo=bound_value(r.problem.column_lower[2])
        @test changed==BitVector([true,true])
        @test Q(lo)<=1-3Q(hi)<0
        @test Q(nextfloat(lo))>1-3Q(hi)
        r2=JSimplex.propagate_row_bounds(r.problem)
        @test r2.problem.column_upper==r.problem.column_upper
        @test r2.problem.column_lower==r.problem.column_lower
    end
end

@testset "Float32 and Float64 directed presolve restore the original LP" begin
    for T in (Float32,Float64), algorithm in (:primal,:dual)
        p=LinearProblem(sparse(reshape(T[3,1],1,2)),T[-1,0];row_upper=T[1],column_lower=T[0,0])
        before=deepcopy(p)
        options=SolverOptions(T;algorithm,pricing=:devex,basis_update=:huangfu_hall,
            basis_refactorization=:native,refactorization_interval=160,presolve=true,scaling=:off,
            simplex_strategy=:legacy,primal_tolerance=T(1e-7),dual_tolerance=T(1e-7),
            time_limit=Inf,iteration_limit=typemax(Int),verbose=false)
        r=solve(p;options)
        @test r.status==OPTIMAL
        if r.status==OPTIMAL
            @test JSimplex._original_primal_feasible(p,r.primal,options.primal_tolerance)
            @test isapprox(r.objective_value,-T(1)/T(3);atol=options.primal_tolerance,rtol=0)
            @test p.A==before.A && p.column_lower==before.column_lower && p.column_upper==before.column_upper
            @test p.objective==before.objective && p.objective_constant==before.objective_constant
        end
    end
end

@testset "Non-nearest hardware rounding keeps exact propagation" begin
    old = Base.Rounding.rounding_raw(Float64)
    try
        for mode in (RoundDown, RoundUp, RoundToZero)
            Base.Rounding.setrounding_raw(Float64, Base.Rounding.to_fenv(mode))
            for T in (Float32, Float64)
                @test rounding(T) == mode
                p=LinearProblem(sparse(reshape(T[3,1],1,2)),zeros(T,2);row_upper=T[1],column_lower=T[0,0])
                @test !isfinite(JSimplex.propagate_row_bounds(p).problem.column_upper[1])
            end
        end
    finally
        Base.Rounding.setrounding_raw(Float64, old)
    end
end
