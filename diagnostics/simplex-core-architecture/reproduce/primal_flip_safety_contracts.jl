using Test,JSimplex,LinearAlgebra,TOML
include("primal_flip_prototype.jl")
const FA=PrimalFlipPrototype
const JS=JSimplex
@assert Threads.nthreads()==BLAS.get_num_threads()==1
mutable struct FaultContext{C}
    core::C
    fault::Symbol
    used::Bool
    failure::Exception
end
Base.getproperty(c::FaultContext,s::Symbol)=s in (:core,:fault,:used,:failure) ? getfield(c,s) : getproperty(getfield(c,:core),s)
function Base.setproperty!(c::FaultContext,s::Symbol,v)
    s in (:core,:fault,:used,:failure) ? setfield!(c,s,v) : setproperty!(getfield(c,:core),s,v)
end
function FA._flip_certificate(c::FaultContext,ws)
    if !c.used && c.fault in (:infeasible,:inconsistent,:audit_exception)
        c.used=true
        c.fault==:audit_exception && throw(JS._UnreliableBasisSolve())
        c.fault==:infeasible ? (ws.primal[1]=2.0) : (ws.primal[end]+=0.25)
    end
    reliable=FA._flip_certificate(c.core,ws)
    if c.fault==:reject_all || (c.fault==:reject_once && !c.used)
        c.used=true
        return false
    end
    return reliable
end
function FA._flip_apply_kernel!(c::FaultContext,ws,entering,change,column)
    if c.fault==:before_apply_exception && !c.used
        c.used=true
        throw(JS._UnreliableBasisSolve())
    end
    return FA._flip_apply_kernel!(c.core,ws,entering,change,column)
end
function FA._flip_recompute!(c::FaultContext,ws;kwargs...)
    c.fault==:recompute_exception && throw(c.failure)
    return FA._flip_recompute!(c.core,ws;kwargs...)
end

function safety_fixture(fault)
    p=FA.PF.problem(Float64,:flip_chain)
    options=JS.SolverOptions(;algorithm=:primal,pricing=:dantzig,simplex_strategy=:legacy,
        basis_update=:pfi,basis_refactorization=:native,partial_pricing=false,
        iteration_limit=fault==:iteration_limit ? 1 : 100,verbose=false)
    policy=JS.NumericalPolicy(Float64,options)
    events=NamedTuple[]
    failure=ErrorException("owned qualification callback failure")
    observer=function(reason,ws)
        reason in (:flip_completed,:pivot_completed) || return
        push!(events,(;reason,iteration=ws.iterations,coherent=JS._legacy_primal_point_certified(ws),
            primal=copy(ws.primal),states=copy(ws.basis.states)))
        fault==:observer_exception && throw(failure)
    end
    d=JS.SimplexDiagnostics(;observer,kernel_timing=true)
    ws=JS.initialize_workspace(p,options;progress=JS.SimplexProgressContext(p;diagnostics=d,numerical_policy=policy))
    # Metadata only: each applied flip advances once; recompute! also invalidates.
    pool=JS._pricing_pool!(ws,:primal)
    generation=pool.basis_generation
    for key in keys(d.kernel_calls);d.kernel_calls[key]=0;d.kernel_nanoseconds[key]=0;end
    deadline=FA.PF.deadline(ws,d)
    stop=JS._guard_stop_callback(()->begin
        if !isempty(events)
            fault==:deadline_exception && throw(failure)
            fault==:time_limit && return true
        end
        deadline()
    end)
    c=FaultContext(FA.FlipAuditContext(ws),fault,false,JS._UnreliableBasisSolve())
    return (;p,ws,d,events,failure,c,stop,generation)
end

rows=Dict[]
try
@testset "Private flip fallback and publication contracts" begin
    for fault in (:none,:reject_once,:reject_all,:infeasible,:inconsistent,:audit_exception,:before_apply_exception,
                  :time_limit,:iteration_limit,:deadline_exception,:observer_exception,:recompute_exception)
        @testset "$fault" begin
            f=safety_fixture(fault)
            terminal=nothing;caught=nothing
            try
                terminal=FA._flip_optimize!(f.c,f.ws,f.stop,f.ws.options.dual_tolerance;perturb_degenerate=false)
            catch exception
                caught=exception
            end
            @test all(e.coherent for e in f.events)
            @test f.ws.scratch.pricing_pool.basis_generation-f.generation==UInt(f.ws.iterations+f.c.direct_recomputations)
            @test length(f.events)==f.ws.iterations
            if fault in (:deadline_exception,:observer_exception,:recompute_exception)
                @test isnothing(terminal)
                if fault==:observer_exception
                    @test caught isa JS.DiagnosticObserverFailure
                    @test caught.cause===f.failure
                else
                    @test caught===(fault==:deadline_exception ? f.failure : f.c.failure)
                end
                @test f.c.dirty
                @test f.ws.iterations==(fault==:recompute_exception ? 4 : 1)
                @test f.c.direct_recomputations==0
            else
                @test isnothing(caught)
                run=JS._internal_solution(f.ws,terminal)
                if fault in (:time_limit,:iteration_limit)
                    @test run.status==(fault==:time_limit ? JS.TIME_LIMIT : JS.ITERATION_LIMIT)
                    @test isnothing(run.primal) && isnothing(run.objective_value)
                    @test f.c.dirty && f.ws.iterations==1
                    @test f.c.direct_recomputations==f.c.endpoint_refreshes==f.c.candidate_copies==0
                else
                    @test run.status==JS.OPTIMAL && run.primal==ones(4) && run.objective_value==-10
                    @test JS._original_primal_feasible(f.p,run.primal,f.ws.options.primal_tolerance)
                    @test !f.c.dirty && f.ws.iterations==4
                    expected=fault==:none ? 1 : fault==:reject_all ? 4 : 2
                    @test f.c.direct_recomputations==expected
                    @test f.d.kernel_calls[:ftran]==4+expected
                    @test f.d.kernel_calls[:btran]==expected
                    @test f.c.endpoint_refreshes==(fault==:reject_all ? 0 : 1)
                end
            end
            push!(rows,Dict("fault"=>string(fault),"iterations"=>f.ws.iterations,"dirty"=>f.c.dirty,
                "direct_recomputations"=>f.c.direct_recomputations,"endpoint_refreshes"=>f.c.endpoint_refreshes,
                "candidate_copies"=>f.c.candidate_copies,"exception"=>string(typeof(caught))))
        end
    end
end
@testset "Private scope, before-write overflow and unsupported precision" begin
    f=safety_fixture(:none)
    @test !FA._flip_eligible(f.c,f.ws,1,0.0)
    @test !FA._flip_eligible(f.c,f.ws,1,Inf)
    before=(copy(f.ws.primal),copy(f.ws.basis.states),f.ws.scratch.pricing_pool.basis_generation)
    f.ws.primal[end]=floatmax(Float64)
    saved=copy(f.ws.primal)
    @test !FA._flip_apply!(f.c,f.ws,1,1.0,[-floatmax(Float64)])
    @test f.ws.primal==saved && f.ws.basis.states==before[2]
    @test f.ws.scratch.pricing_pool.basis_generation==before[3]
    @test f.c.applied==0 && !f.c.dirty
    other=safety_fixture(:none)
    @test_throws ErrorException FA._flip_iteration!(f.c,other.ws,other.stop,other.ws.options.dual_tolerance)
    @test !FA.eligible_run(JS._candidate_workspace(other.ws))
    @test_throws MethodError FA.run_flip_experiment!(Float64,:flip_chain;stop_requested=()->false)
    @test_throws MethodError FA.run_flip_experiment!(Float64,:flip_chain;observer=identity)
    @test_throws MethodError FA.run_flip_experiment!(Float64,:flip_chain;costs=[0.0])
    @test_throws MethodError FA.run_flip_experiment!(Float64,:flip_chain;bounds=[0.0])
    for T in (BigFloat,Rational{Int64},Rational{BigInt})
        out=FA.run_flip_experiment!(T,:flip_chain)
        @test !out.enabled && out.stats.applied==out.stats.skips==0
        @test out.run.status==JS.OPTIMAL && out.feasible
        @test out.calls[:ftran]==8 && out.calls[:btran]==4
    end
end
finally
    open(io->TOML.print(io,Dict("cases"=>rows,"source_hashes"=>FA.SOURCE_HASHES,
        "rewritten_hashes"=>FA.REWRITTEN_HASHES)),only(ARGS),"w")
end
