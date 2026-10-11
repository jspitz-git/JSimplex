using Test,JSimplex,LinearAlgebra,TOML
include("primal_flip_prototype.jl")
const FA=PrimalFlipPrototype
const JS=JSimplex
@assert Threads.nthreads()==BLAS.get_num_threads()==1
const OUTPUT=only(ARGS)
ispath(OUTPUT) && error("Do not overwrite an attempt")
rows=Dict[]
try
    @testset "Private audited-flip characterized branches" begin
        for T in (Float32,Float64),manager in FA.PF.MANAGERS,backend in FA.PF.BACKENDS,kind in FA.PF.KINDS
            @testset "$T/$manager/$backend/$kind" begin
                out=FA.run_flip_experiment!(T,kind;manager,backend)
                run,s=out.run,out.stats
                @test out.enabled && !s.dirty
                @test run.status==(kind==:flip_then_unbounded ? JS.UNBOUNDED : JS.OPTIMAL)
                expected_events=kind==:flip_chain ? fill("flip_completed",4) :
                    kind==:flip_then_pivot ? ["flip_completed","pivot_completed"] : ["flip_completed"]
                @test getproperty.(out.events,:event)==expected_events
                @test all(!iszero(parse(T,e.step)) for e in out.events)
                @test out.iterations==(kind in (:flip_then_pivot,:scheduled_flip) ? 2 : kind==:flip_chain ? 4 : 1)
                @test s.applied==(kind==:flip_chain ? 4 : 1)
                expected_ftran=kind==:flip_chain ? 5 : kind==:flip_then_pivot ? 3 : kind==:flip_then_unbounded ? 4 : 2
                expected_btran=kind==:flip_then_pivot ? 2 : 1
                @test out.calls[:ftran]==expected_ftran
                @test out.calls[:btran]==expected_btran
                @test s.endpoint_refreshes==(kind in (:flip_chain,:flip_then_unbounded) ? 1 : 0)
                @test s.skips==(kind==:scheduled_flip ? 0 : kind==:flip_chain ? 4 : 1)
                @test s.fallbacks==0
                if run.status==JS.OPTIMAL
                    point=kind==:flip_chain ? ones(T,4) : kind==:flip_then_pivot ? T[1,4] : T[1,1]
                    objective=kind==:flip_chain ? -10 : kind==:flip_then_pivot ? -6 : -5
                    @test out.feasible && run.primal==point && run.objective_value==T(objective)
                else
                    @test isnothing(run.primal) && isnothing(run.objective_value)
                end
                push!(rows,Dict("type"=>string(T),"fixture"=>string(kind),"manager"=>string(manager),
                    "backend"=>string(backend),"status"=>string(run.status),"stats"=>Dict(string(k)=>v for (k,v) in pairs(s)),
                    "kernel_calls"=>Dict(string(k)=>v for (k,v) in out.calls)))
            end
        end
    end
finally
    open(io->TOML.print(io,Dict("source_hashes"=>FA.SOURCE_HASHES,"rewritten_hashes"=>FA.REWRITTEN_HASHES,
        "results"=>rows,"returned_cases"=>length(rows),"expected_cases"=>80)),OUTPUT,"w")
end
