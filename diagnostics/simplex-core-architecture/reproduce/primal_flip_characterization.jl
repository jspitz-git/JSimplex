# Run only after S0 releases the exclusive guard. Arguments: output.toml
# Control branch census, not an elapsed/allocation benchmark or a prototype.
using Test, JSimplex, LinearAlgebra, TOML, SHA
include("primal_flip_fixtures.jl")
const PF = PrimalFlipFixtures
const JS = JSimplex
const ROOT = realpath(joinpath(@__DIR__, "../../.."))
@assert realpath(dirname(dirname(pathof(JS)))) == ROOT
@assert Threads.nthreads() == BLAS.get_num_threads() == 1
length(ARGS) == 1 || error("Expected a new output TOML path")
ispath(ARGS[1]) && error("Do not overwrite an existing attempt")
const ROWS = Dict{String,Any}[]
const SOURCE_HASHES = Dict(relpath(joinpath(dir, file), ROOT) =>
    bytes2hex(open(sha256, joinpath(dir, file)))
    for (dir, _, files) in walkdir(joinpath(ROOT, "src")) for file in files)

function characterize(T, kind, manager, backend)
    fixture = PF.workspace(T, kind; manager, backend)
    ws, diagnostics = fixture.ws, fixture.diagnostics
    initial_iteration, initial_refactors = ws.iterations, ws.refactorizations
    initial_basis = copy(ws.basis.basic_indices)
    initial_prices = copy(ws.reduced_costs)
    terminal = JS._primal_optimize!(ws, PF.deadline(ws, diagnostics),
        ws.options.dual_tolerance; perturb_degenerate=false)
    # Keep optimizer work separate from final certificate work.
    optimizer_calls = copy(diagnostics.kernel_calls)
    optimizer_events = copy(diagnostics.counts)
    run = JS._internal_solution(ws, terminal)
    events = fixture.events
    expected = kind == :flip_then_pivot ? ["flip_completed", "pivot_completed"] :
        kind == :flip_chain ? fill("flip_completed", 4) : ["flip_completed"]
    @test getproperty.(events, :event) == expected
    @test all(!iszero(parse(T, event.step)) for event in events)
    @test ws.iterations - initial_iteration == length(expected)
    @test all(event.selected_row == 0 for event in events if event.event == "flip_completed")
    @test terminal.status == (kind == :flip_then_unbounded ? JS.UNBOUNDED : JS.OPTIMAL)
    @test run.status == terminal.status
    if kind != :flip_then_pivot
        @test ws.basis.basic_indices == initial_basis
        @test ws.reduced_costs == initial_prices
    end
    if kind == :scheduled_flip
        @test ws.refactorizations == initial_refactors + 1
        @test optimizer_events[:refactor_limit] == 1
        @test all(count == 0 for (event, count) in optimizer_events
            if startswith(string(event), "refactor_") && event != :refactor_limit)
        @test isempty(ws.factorization.updates)
        @test ws.primal[1:2] == T[1, 1]
    else
        @test ws.refactorizations == initial_refactors
    end
    feasible = !isnothing(run.primal) &&
        JS._original_primal_feasible(fixture.problem, run.primal, ws.options.primal_tolerance)
    if run.status == JS.OPTIMAL
        @test feasible
        expected_point = kind == :flip_then_pivot ? T[1, 4] :
            kind == :flip_chain ? ones(T, 4) : T[1, 1]
        expected_objective = kind == :flip_then_pivot ? T(-6) :
            kind == :flip_chain ? T(-10) : T(-5)
        @test run.primal == expected_point
        @test run.objective_value == expected_objective
    else
        @test isnothing(run.primal) && isnothing(run.objective_value)
    end
    # Legacy flip-only control reconstructs after each flip. Additional work
    # must be explained if source characterization disproves this expectation.
    if kind == :flip_chain
        @test optimizer_calls[:ftran] == 8
        @test optimizer_calls[:btran] == 4
    end
    return Dict{String,Any}("type"=>string(T), "fixture"=>string(kind),
        "manager"=>string(manager), "backend"=>string(backend),
        "status"=>string(run.status), "objective"=>string(run.objective_value),
        "primal"=>isnothing(run.primal) ? String[] : string.(run.primal),
        "original_primal_feasible"=>feasible, "iterations"=>ws.iterations,
        "initial_iteration"=>initial_iteration, "initial_refactors"=>initial_refactors,
        "refactors"=>ws.refactorizations,
        "events"=>[Dict(string(k)=>v for (k,v) in pairs(e)) for e in events],
        "preparation"=>[Dict(string(k)=>v for (k,v) in pairs(e)) for e in fixture.preparation],
        "optimizer_kernel_calls"=>Dict(string(k)=>v for (k,v) in optimizer_calls),
        "optimizer_event_counts"=>Dict(string(k)=>v for (k,v) in optimizer_events),
        "total_kernel_calls"=>Dict(string(k)=>v for (k,v) in diagnostics.kernel_calls))
end

try
    @testset "Original legacy primal flip branch census" begin
        for T in (Float32, Float64), manager in PF.MANAGERS,
            backend in PF.BACKENDS, kind in PF.KINDS
            @testset "$T/$manager/$backend/$kind" begin
                push!(ROWS, characterize(T, kind, manager, backend))
            end
        end
    end
finally
    # Preserve partial findings if a fixture assumption or test fails.
    open(ARGS[1], "w") do io
        TOML.print(io, Dict("schema_version"=>1, "source_hashes"=>SOURCE_HASHES,
            "purpose"=>"control characterization; no speedup or prototype acceptance",
            "julia_version"=>string(VERSION), "expected_cases"=>80,
            "returned_cases"=>length(ROWS), "results"=>ROWS))
    end
end
