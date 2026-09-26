using SparseArrays, Random

@testset "Legacy bound flipping consumes only the required breakpoints" begin
    rng = MersenneTwister(1507)
    costs = Float64.(randperm(rng,4096))
    problem = LinearProblem(spzeros(1,4096),costs;column_upper=ones(4096))
    ws = JSimplex.initialize_workspace(problem,SolverOptions(verbose=false))
    row = [ones(4096);0.0]
    run(v) = JSimplex._bound_flipping_ratio_test(ws,row,1.0,v)
    enter,flips,exhausted = run(0.5)
    @test enter == findfirst(==(1.0),costs)
    @test isempty(flips) && !exhausted
    @test (@allocated run(0.5)) <= 4096
    enter,flips,exhausted = run(3.5)
    @test enter == findfirst(==(4.0),costs)
    @test flips == [findfirst(==(Float64(k)),costs) for k in 1:3]
    @test !exhausted
    enter,flips,exhausted = run(5000.0)
    @test enter == -1 && exhausted
    @test flips == sortperm(costs)
end

@testset "Legacy breakpoints preserve signed-zero and stable ties" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        costs = T[0,0,1,1]
        T <: AbstractFloat && (costs[2] = -zero(T))
        ws = JSimplex.initialize_workspace(
            LinearProblem(spzeros(T,1,4),costs;column_upper=ones(T,4)),
            SolverOptions(T;verbose=false))
        ws.reduced_costs[1:4] .= costs
        enter,flips,exhausted = JSimplex._bound_flipping_ratio_test(ws,T[1,1,1,1,0],one(T),T(5//2))
        @test enter == 3
        @test flips == (T <: AbstractFloat ? [2,1] : [1,2])
        @test !exhausted
    end
end
