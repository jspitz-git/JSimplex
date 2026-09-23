@testset "Stagnation requires two windows without scaled progress" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        monitor = JSimplex.StagnationMonitor{T}(64)
        tiny = T <: Rational ? one(T)/big(10)^30 : T(1e-30)
        states = Symbol[]
        for i in 1:128
            push!(states,JSimplex.observe_progress!(monitor;objective=one(T),
                primal_violation=one(T),dual_violation=zero(T),
                primal_step=tiny,dual_step=tiny))
        end
        @test states[63] == :progress
        @test states[64] == :watch
        @test states[127] == :watch
        @test states[128] == :stalled
        @test monitor.observations == 128
        @test monitor.stalled_windows == 2
        JSimplex.reset_stagnation!(monitor)
        @test monitor.state == :progress
        @test monitor.window_count == 0
    end
end

@testset "Slow measurable progress accumulates across a watched window" begin
    monitor = JSimplex.StagnationMonitor{Float64}(4;tolerance=0.001)
    for objective in (1.0,0.99975,0.99950,0.99925)
        JSimplex.observe_progress!(monitor;objective,primal_violation=1.0,
            dual_violation=0.0,primal_step=0.0,dual_step=0.0)
    end
    @test monitor.state == :watch
    for objective in (0.999,0.998875,0.998625,0.99850)
        JSimplex.observe_progress!(monitor;objective,primal_violation=1.0,
            dual_violation=0.0,primal_step=0.0,dual_step=0.0)
    end
    @test monitor.state == :progress
end

@testset "Stagnation history stays bounded and exact comparisons stay exact" begin
    monitor = JSimplex.StagnationMonitor{Float64}(8)
    observe() = JSimplex.observe_progress!(monitor;objective=1.0,
        primal_violation=1.0,dual_violation=0.0,primal_step=0.0,dual_step=0.0)
    for _ in 1:32; observe(); end
    retained = Base.summarysize(monitor)
    for _ in 1:4096; observe(); end
    @test Base.summarysize(monitor) == retained
    @test monitor.state == :stalled
    @test_throws ArgumentError JSimplex.observe_progress!(monitor;objective=NaN,
        primal_violation=1.0,dual_violation=0.0,primal_step=0.0,dual_step=0.0)
    @test monitor.state == :stalled
    exact = JSimplex.StagnationMonitor{Rational{Int64}}(2)
    JSimplex.observe_progress!(exact;objective=typemax(Int64)//1,
        primal_violation=1//1,dual_violation=0//1,primal_step=0//1,dual_step=0//1)
    JSimplex.observe_progress!(exact;objective=-typemax(Int64)//1,
        primal_violation=1//1,dual_violation=0//1,primal_step=0//1,dual_step=0//1)
    @test exact.state == :progress
    @test exact.objective_improvement == 2big(typemax(Int64))//1
    @test exact.objective_improvement isa Rational{BigInt}
end

@testset "Real objective or feasibility progress prevents stagnation" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), improving in (:objective,:primal,:dual)
        monitor = JSimplex.StagnationMonitor{T}(8)
        for i in 1:64
            value = T(65-i)
            state = JSimplex.observe_progress!(monitor;
                objective=improving == :objective ? value : one(T),
                primal_violation=improving == :primal ? value : one(T),
                dual_violation=improving == :dual ? value : zero(T),
                primal_step=zero(T),dual_step=zero(T))
            @test state == :progress
        end
    end
end

@testset "Oscillation and large steps do not establish net progress" begin
    monitor = JSimplex.StagnationMonitor{Float64}(8)
    for i in 1:32
        JSimplex.observe_progress!(monitor;objective=isodd(i) ? 1.0 : 2.0,
            primal_violation=1.0,dual_violation=0.0,primal_step=10.0,dual_step=10.0)
    end
    @test monitor.state == :stalled
    @test monitor.minimum_objective == 1.0
    @test monitor.start_objective == 1.0
    @test monitor.end_objective == 2.0
    @test monitor.insignificant_steps == 0
end

@testset "Progress normalization uses explicit working scales" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        left = JSimplex.StagnationMonitor{T}(8)
        right = JSimplex.StagnationMonitor{T}(8;objective_scale=T(128),
            primal_scale=T(16),dual_scale=T(4))
        for i in 1:64
            objective = T(65-i)
            a = JSimplex.observe_progress!(left;objective,primal_violation=one(T),
                dual_violation=one(T),primal_step=one(T),dual_step=one(T))
            b = JSimplex.observe_progress!(right;objective=128*objective,
                primal_violation=T(16),dual_violation=T(4),primal_step=T(16),dual_step=T(4))
            @test a == b == :progress
        end
    end
    @test_throws ArgumentError JSimplex.StagnationMonitor{Float64}(0)
    @test_throws ArgumentError JSimplex.StagnationMonitor{Float64}(8;objective_scale=0.0)
end
