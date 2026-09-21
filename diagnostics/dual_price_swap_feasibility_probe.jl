# Throwaway feasibility probe: source overrides live in this Julia process only.
using JSimplex, SparseArrays, LinearAlgebra, Logging, Test, TOML
include(joinpath(pwd(), "dev", "allocations.jl"))
using .JSimplexAllocations: measure_allocations
mode = ARGS[1]
source = read("src/dual_simplex.jl", String)
function definition(name)
    start = findfirst("function $name(workspace::SimplexWorkspace{Float64}", source).start
    stop = findnext("\n$name(::SimplexWorkspace", source, start).start
    return source[start:prevind(source, stop)]
end
if mode == "swap"
    prices = definition("_try_refine_dual_prices!")
    prices = replace(prices,
        "old_prices = copy(workspace.reduced_costs)" => "old_prices = workspace.reduced_costs",
        "workspace.reduced_costs .= replacement" => "workspace.reduced_costs = replacement",
        "workspace.reduced_costs .= old_prices" => "workspace.reduced_costs = old_prices")
    pivot = definition("_try_refine_dual_pivot!")
    pivot = replace(pivot,
        "previous_prices = copy(workspace.reduced_costs)" => "previous_prices = workspace.reduced_costs",
        "copyto!(workspace.reduced_costs, prices)" => "workspace.reduced_costs = prices",
        "accepted || copyto!(workspace.reduced_costs, previous_prices)" =>
            "accepted || (workspace.reduced_costs = previous_prices)")
    Base.include_string(JSimplex, prices * "\n" * pivot, "throwaway-dual-price-swap.jl")
end
function setup_pivot(n; method=:pfi)
    p = LinearProblem(spdiagm(0=>ones(n)), ones(n); row_lower=ones(n))
    w = JSimplex.initialize_workspace(p, SolverOptions(; verbose=false, basis_update=method))
    w.reduced_costs[1] = 1.1
    return w
end
function setup_prices(n; method=:pfi)
    p = LinearProblem(spdiagm(0=>ones(n)), zeros(n); row_upper=fill(2.0,n), column_upper=ones(n))
    w = JSimplex.initialize_workspace(p, SolverOptions(; verbose=false, basis_update=method))
    w.basis.states[1] = JSimplex.AT_UPPER
    w.costs[1] = 4e-7
    w.perturbed = true
    JSimplex.recompute!(w)
    return w
end
nothing_stop() = false
pivot_run(w) = (JSimplex._try_refine_dual_pivot!(w, 1, -1.0, 1.0, nothing_stop); nothing)
prices_run(w) = (JSimplex._try_refine_dual_prices!(w, nothing_stop); nothing)
rows = Dict{String,Any}[]
with_logger(NullLogger()) do
    @testset "Throwaway price swap feasibility" begin
        for method in (:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub), n in (2,64)
            w=setup_prices(n; method); old=w.reduced_costs; saved=copy(old)
            @test JSimplex._try_refine_dual_prices!(w, nothing_stop)
            @test w.costs[1] == 0.0
            @test iszero(JSimplex.dual_infeasibility(w))
            @test w.reduced_costs[1] == 0.0
            if mode == "swap"
                @test w.reduced_costs !== old
                @test old == saved
            end
            for outcome in (:accept,:reject,:stop,:throw)
                w=setup_pivot(n; method); old=w.reduced_costs; saved=copy(old)
                callback = () -> begin
                    if w.reduced_costs[1] == 1.0
                        outcome == :throw && error("probe stop failure")
                        outcome == :stop && return true
                    end
                    false
                end
                if outcome == :throw
                    @test_throws ErrorException JSimplex._try_refine_dual_pivot!(w,1,-1.0,1.0,callback)
                else
                    result=JSimplex._try_refine_dual_pivot!(w,1,outcome == :reject ? 1.0 : -1.0,1.0,callback)
                    @test outcome == :accept ? result.entering_index == 1 : isnothing(result)
                end
                if outcome != :accept
                    @test w.reduced_costs === old
                    @test old == saved
                else
                    @test w.reduced_costs[1] == 1.0
                    mode == "swap" && (@test old == saved)
                end
            end
        end
    end
    for n in (2,64,512), (name,setup,run) in (("prices",setup_prices,prices_run),("pivot",setup_pivot,pivot_run))
        row=measure_allocations(run; setup=()->setup(n), samples=3)
        merge!(row,Dict("case"=>name,"rows"=>n,"prices"=>2n))
        push!(rows,row)
        println(name," n=",n," ",row); flush(stdout)
    end
end
open(io->TOML.print(io,Dict("mode"=>mode,"rows"=>rows);sorted=true),"diagnostics/dual-price-swap-$(mode).toml","w")
if mode == "swap"
    @testset "Dual suite with throwaway swap" begin
        include(joinpath(pwd(), "test", "dual_simplex_tests.jl"))
    end
end
