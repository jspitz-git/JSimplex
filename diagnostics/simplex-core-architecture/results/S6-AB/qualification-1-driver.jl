using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
const JS=JSimplex
const ROOT=dirname(dirname(pathof(JS)))
const FILE=joinpath(ROOT,"test/native_phase_transfer_tests.jl")
const SOURCE=read(FILE,String)
const HELPER="function reliable_artificial_exchange_fixture"*first(split(split(SOURCE,"function reliable_artificial_exchange_fixture";limit=2)[2],"\n@testset";limit=2))
Base.include_string(@__MODULE__,HELPER,FILE)
const RECORDS=Dict[]
fields(x)=Dict(string(k)=>repr(getfield(x,k)) for k in fieldnames(typeof(x)))
mutable struct PhaseBoundaryFactor{T,F}
    inner::F
    rhs::Vector{T}
    armed::Bool
    hits::Int
    updates_seen::Int
    refs::Int
    invalidations::Int
    calls::Vector{Dict}
end
Base.getproperty(f::PhaseBoundaryFactor,k::Symbol)=k in fieldnames(typeof(f)) ? getfield(f,k) : getproperty(getfield(f,:inner),k)
function solve_record!(dest,f,rhs,kind)
    saved=copy(rhs)
    kind==:ordinary ? JS._ordinary_forward_solve!(dest,f.inner,rhs) :
      kind==:prepared ? JS.forward_solve!(dest,f.inner,rhs) : JS.transpose_solve!(dest,f.inner,rhs)
    actual=copy(dest); hit=false
    if f.armed && kind==:ordinary && saved==f.rhs
        @assert f.refs==1 && f.updates_seen==1 && f.hits==0 && actual==f.rhs
        dest[3]+=eltype(dest)(2)^(-10)
        f.armed=false;f.hits+=1;hit=true
    end
    push!(f.calls,Dict("kind"=>string(kind),"rhs"=>Float64.(saved),"real_output"=>Float64.(actual),"output"=>Float64.(dest),"hit"=>hit,"refactors"=>f.refs,"updates"=>f.updates_seen))
    dest
end
JS._ordinary_forward_solve!(dest::Vector{T},f::PhaseBoundaryFactor{T},rhs::AbstractVector) where T=solve_record!(dest,f,rhs,:ordinary)
JS.forward_solve!(dest::Vector{T},f::PhaseBoundaryFactor{T},rhs::AbstractVector) where T=solve_record!(dest,f,rhs,:prepared)
JS.transpose_solve!(dest::Vector{T},f::PhaseBoundaryFactor{T},rhs::AbstractVector) where T=solve_record!(dest,f,rhs,:transpose)
function JS._invalidate_prepared_destination!(f::PhaseBoundaryFactor,dest)
    f.invalidations+=1
    JS._invalidate_prepared_destination!(f.inner,dest)
end
JS._finite_updated_factor(f::PhaseBoundaryFactor)=JS._finite_updated_factor(f.inner)
function JS.replace_column!(f::PhaseBoundaryFactor,direction::AbstractVector,row::Integer;kwargs...)
    f.armed=false
    @assert row==6 && direction==[0,0,0,0,0,1]
    result=JS.replace_column!(f.inner,direction,row;kwargs...)
    f.updates_seen+=1
    result
end
function JS.refactorize!(f::PhaseBoundaryFactor{T},B::AbstractMatrix) where T
    f.armed=false
    @assert B==Matrix{T}(I,6,6) && f.updates_seen==1
    result=JS.refactorize!(f.inner,B)
    f.refs+=1
    f.armed=f.refs==1 && f.hits==0
    result
end
JS.copy_basis_factorization(f::PhaseBoundaryFactor)=error("Copy is outside the S6-AB native boundary scope")
function wrap_phase(ws)
    @assert !ws.progress.numerical_policy.hypersparse && !ws.progress.numerical_policy.solve_refinement && !ws.progress.numerical_policy.recovery
    T=eltype(ws.primal);f=PhaseBoundaryFactor(ws.factorization,T[1,1,0,0,0,0],false,0,0,0,0,Dict[])
    JS.SimplexWorkspace((k==:factorization ? f : getfield(ws,k) for k in fieldnames(typeof(ws)))...)
end
function state(ws)
 Dict("basis"=>copy(ws.basis.basic_indices),"states"=>string.(ws.basis.states),"primal"=>Float64.(ws.primal),"rho"=>Float64.(ws.scratch.rho),"iterations"=>ws.iterations,"refactorizations"=>ws.refactorizations,"factor"=>string(typeof(ws.factorization)))
end
function counts(f)
 calls=f.calls
 Dict("ftran"=>count(c->c["kind"]!="transpose",calls),"btran"=>count(c->c["kind"]=="transpose",calls),"primal_rhs"=>count(c->c["kind"]!="transpose" && c["rhs"]==[1,1,0,0,0,0],calls),"correction_rhs"=>count(c->c["kind"]!="transpose" && c["rhs"]==[0,0,-2.0^-10,0,0,0],calls),"update"=>f.updates_seen,"refactor"=>f.refs,"hit"=>f.hits,"invalidations"=>f.invalidations)
end
work_ok(c)=all(c[k]==v for (k,v) in ("ftran"=>4,"btran"=>2,"primal_rhs"=>1,"correction_rhs"=>1,"update"=>1,"refactor"=>1,"hit"=>1))
function run_case(T,manager,subject)
    events=Dict[]
    observer=(event,ws)->begin
        if ws isa JS.SimplexWorkspace
            push!(events,Dict("event"=>string(event),"columns"=>size(ws.problem.A,2),"wrapped"=>ws.factorization isa PhaseBoundaryFactor,"state"=>state(ws)))
        else
            push!(events,Dict("event"=>string(event),"columns"=>-1,"wrapped"=>false))
        end
    end
    d=JS.SimplexDiagnostics(;observer,kernel_timing=true)
    phase,map,original,policy=reliable_artificial_exchange_fixture(T,manager;diagnostics=d)
    subject && (phase=wrap_phase(phase))
    originalfactor=original.factorization
    @test !(originalfactor isa PhaseBoundaryFactor)
    @test JS._legacy_primal_point_certified(phase)
    r=Dict("scalar"=>string(T),"manager"=>string(manager),"subject"=>subject,"options"=>fields(phase.options),"policy"=>fields(policy),"before_phase"=>state(phase),"before_original"=>state(original))
    empty!(events);before=copy(d.kernel_calls);counts_before=copy(d.counts)
    accepted=false
    try
        accepted=JS.remove_artificials!(phase,map,original,policy,()->false)
    finally
        r["accepted"]=accepted;r["phase"]=state(phase);r["original"]=state(original)
        r["events"]=copy(events);r["kernels"]=Dict(string(k)=>v-get(before,k,0) for (k,v) in d.kernel_calls)
        r["event_counts"]=Dict(string(k)=>v-get(counts_before,k,0) for (k,v) in d.counts)
        if subject
            r["calls"]=copy(phase.factorization.calls);r["work"]=counts(phase.factorization)
        end
        push!(RECORDS,r)
    end
    @test accepted
    if accepted
        @test original.iterations==1
        @test original.basis.basic_indices==collect(1:6)
        @test JS._recomputed_basis_reliable(original)
        @test JS._legacy_primal_point_certified(original)
        feasible=JS._original_primal_feasible(original,original.primal[1:6]);r["post_certificate"]=feasible
        @test feasible
    end
    @test original.primal==T[1,1,0,0,0,0,1,1,0,0,0,0]
    @test !(original.factorization isa PhaseBoundaryFactor)
    @test all(!e["wrapped"] for e in events if e["columns"]==6)
    @test original.factorization!==originalfactor
    @test r["kernels"]["ftran"]==(subject ? 6 : 5)
    @test r["kernels"]["btran"]==4
    @test r["kernels"]["refactorization"]==2
    @test r["event_counts"]["correction_attempt"]==(subject ? 1 : 0)
    if subject
        @test work_ok(r["work"])
        @test r["work"]["invalidations"]==5
        phase_events=[e["event"] for e in events if e["wrapped"]]
        @test phase_events==["refactor_other","correction_attempt","artificial_removed"]
        bad=copy(r["work"]);bad["ftran"]+=1;bad["primal_rhs"]+=1
        r["negative_work"]=bad;r["negative_rejected"]=!work_ok(bad)
        @test !work_ok(bad)
        injected=only(filter(c->c["hit"],r["calls"]))
        @test injected["real_output"]==[1,1,0,0,0,0] && injected["output"]==[1,1,2.0^-10,0,0,0]
        corrected=only(filter(c->c["rhs"]==[0,0,-2.0^-10,0,0,0],r["calls"]))
        @test corrected["real_output"]==corrected["output"]==[0,0,-2.0^-10,0,0,0]
    end
end
const GLOBALS=(precision(BigFloat),rounding(BigFloat),get_zero_subnormals())
@assert !ispath(only(ARGS))
try
 @testset "S6-AB phase reconstruction boundary" begin
    for T in (Float32,Float64),manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub),subject in (false,true)
        run_case(T,manager,subject)
    end
    @test GLOBALS==(precision(BigFloat),rounding(BigFloat),get_zero_subnormals())
 end
finally
 open(only(ARGS),"w") do io
    TOML.print(io,Dict("source"=>pathof(JS),"test_sha256"=>bytes2hex(sha256(SOURCE)),"helper"=>HELPER,"records"=>RECORDS,"julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH),"julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),"globals_preserved"=>GLOBALS==(precision(BigFloat),rounding(BigFloat),get_zero_subnormals())))
 end
end
