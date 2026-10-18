# UNEXECUTED. New Task3 matched-policy whole-lifecycle measurement. No production overwrite.
using JSimplex, LinearAlgebra, SparseArrays, TOML, PrecompileTools
const J = JSimplex
include("probe.jl")
const PHASE, OUTPUT, PROJECT = ARGS
require(v,s) = v || error(s)
token(x::Float64) = string(reinterpret(UInt64,x);base=16,pad=16)
number(s) = reinterpret(Float64,parse(UInt64,s;base=16))
function save(name,data)
    p=joinpath(OUTPUT,name);require(!ispath(p),"Existing output")
    open(p,"w") do io; TOML.print(io,data);flush(io);end
end
function decode_fixture(f)
    mats=[SparseMatrixCSC(m["n"],m["n"],Int.(m["colptr"]),Int.(m["rowval"]),number.(m["nzval"])) for m in f["matrices"]]
    steps=[(j=Int(s["j"]),a=number.(s["a"]),dse=number.(s["dse"]),unit=number.(s["unit"])) for s in f["steps"]]
    return (name=f["name"],n=Int(f["n"]),matrices=mats,steps=steps)
end
function unchanged(f,source)
    all(m.colptr==s["colptr"] && m.rowval==s["rowval"] && token.(m.nzval)==s["nzval"] for (m,s) in zip(f.matrices,source["matrices"])) &&
    all(t.j==s["j"] && token.(t.a)==s["a"] && token.(t.dse)==s["dse"] && token.(t.unit)==s["unit"] for (t,s) in zip(f.steps,source["steps"]))
end
policy(::Val{:native}) = J._NATIVE_PIVOT_ONE
policy(::Val{:markowitz}) = J._NATIVE_PIVOT_DEFAULT
policy_name(::Val{:native}) = "threshold_one"
policy_name(::Val{:markowitz}) = "default"
factory(::Val{:reference},F,B,backend) = J._direct_lu_factor(F,B,backend,policy(backend);normalize=true)
factory(::Val{:candidate},F,B,backend) = J._bgx_factor(B,backend,policy(backend))
mode(::Val{:reference},f) = J._direct_mode(f)
mode(::Val{:candidate},f) = J._direct_mode(f)
# Identical nested timers on both sides; times are subsets of @timed total.
# Detached output destinations are harness-owned and allocated outside both windows.
function lifecycle(F::Type, backend, side, fixture, outputs)
    clocks=zeros(UInt64,6) # construct, FTRAN, BTRAN, update, refactor1, refactor2
    t=time_ns();factor=factory(side,F,fixture.matrices[1],backend);clocks[1]=time_ns()-t
    m0=mode(side,factor);m1=m0;m2=m0
    for k in 1:8
        s=fixture.steps[k];direction=outputs[3k-2];dse=outputs[3k-1];dual=outputs[3k]
        t=time_ns();J.forward_solve!(direction,factor,s.a);clocks[2]+=time_ns()-t
        t=time_ns();J.forward_solve!(dse,factor,s.dse);clocks[2]+=time_ns()-t
        t=time_ns();J.replace_column!(factor,direction,s.j);clocks[4]+=time_ns()-t
        t=time_ns();J.transpose_solve!(dual,factor,s.unit);clocks[3]+=time_ns()-t
        if k==4
            t=time_ns();J.refactorize!(factor,fixture.matrices[5]);clocks[5]=time_ns()-t
            m1=mode(side,factor)
        elseif k==8
            t=time_ns();J.refactorize!(factor,fixture.matrices[9]);clocks[6]=time_ns()-t
            m2=mode(side,factor)
        end
    end
    return factor,clocks,(m0,m1,m2)
end
# No extra factor solves. Preliminary Float64 residual check outside timing;
# independent auditor evaluates every recorded output exactly from binary tokens.
function residual_ok(M,x,rhs,transposed)
    all(isfinite,x) || return false
    A=transposed ? transpose(M) : M
    bound=128*length(x)*eps(Float64)*max(1.,opnorm(A,Inf)*norm(x,Inf),norm(rhs,Inf))
    norm(A*x-rhs,Inf)<=bound
end
function window(F,backend,side,f,source,pair,order,outputs)
    timed=@timed lifecycle(F,backend,side,f,outputs)
    factor,clocks,modes=timed.value
    # Keep only this final factor until checks/graph accounting, no old factors.
    retained=Base.summarysize(factor)
    inputs_ok=unchanged(f,source);ok=inputs_ok
    for k in 1:8
        s=f.steps[k]
        ok &= residual_ok(f.matrices[k],outputs[3k-2],s.a,false)
        ok &= residual_ok(f.matrices[k],outputs[3k-1],s.dse,false)
        ok &= residual_ok(f.matrices[k+1],outputs[3k],s.unit,true)
    end
    allowed=(:normalized,:direct,:fallback)
    ok &= all(m->m in allowed,modes)
    row=Dict{String,Any}("pair"=>pair,"order"=>order,"measured"=>pair>3,
        "side"=>side===Val(:candidate) ? "candidate" : "reference",
        "policy"=>policy_name(backend),
        "seconds"=>timed.time,"bytes"=>timed.bytes,"events"=>Base.gc_alloc_count(timed.gcstats),
        "gc_seconds"=>timed.gctime,"compile_seconds"=>timed.compile_time,"recompile_seconds"=>timed.recompile_time,
        "nested_seconds"=>Float64.(clocks)./1e9,"retained_bytes"=>retained,
        "modes"=>string.(collect(modes)),"inputs_unchanged"=>inputs_ok,"correct"=>ok,
        "outputs"=>[token.(x) for x in outputs])
    return row
end
# Untimed bounded controls on B0/B4/B8: two constructions + four refactors/cell.
# The exporter records detached tokens only; it never retains a backend owner.
function observe_backend(b,backend)
    if backend===Val(:native)
        require(b isa J.UMFPACKBackend && b.pivot_policy===policy(backend),"Native preflight intent")
        control=b.factorization.control
        expected=SparseArrays.UMFPACK.get_umfpack_control(Float64,Int)
        expected[SparseArrays.LibSuiteSparse.UMFPACK_PIVOT_TOLERANCE+1]=1.0
        expected[SparseArrays.LibSuiteSparse.UMFPACK_IRSTEP+1]=0.0
        require(length(control)==20 && isequal(control,expected),"Actual native controls")
        strategy=b.factorization.info[SparseArrays.LibSuiteSparse.UMFPACK_STRATEGY_USED+1]
        require(isfinite(strategy),"Actual native strategy")
        return Dict("kind"=>"native","policy"=>policy_name(backend),"control"=>token.(control),"expected_control"=>token.(expected),"strategy"=>token(strategy))
    end
    require(b isa J.MarkowitzBackend{Float64} && policy(backend)===J._NATIVE_PIVOT_DEFAULT,"Markowitz preflight")
    return Dict("kind"=>"markowitz","policy"=>"default","control"=>String[],"expected_control"=>String[],"strategy"=>"")
end
function preflight(F,backend,f,source)
    refs=Dict[];cands=Dict[];modes=String[]
    reference_exporter=b->begin
        push!(refs,observe_backend(b,backend));J._export_basis_lu(b)
    end
    ordinary=J._direct_lu_factor_with_exporter(F,f.matrices[1],backend,policy(backend),reference_exporter;normalize=true)
    function exporter(b,o;allocate=J._bgx_allocate)
        push!(cands,observe_backend(b,backend))
        J._bgx_export(b,o;allocate)
    end
    owner=J._BGXBuildOwner(nothing)
    inner=J._bgx_build(f.matrices[1],backend,policy(backend),true,owner;export_parts=exporter)
    candidate=J.BGExportFactor(inner,owner.workspace,false)
    require(J._direct_mode(ordinary)==J._direct_mode(candidate),"Preflight paired modes")
    push!(modes,string(J._direct_mode(candidate)))
    require(candidate.inner.base.pivot_policy===policy(backend),"Candidate preflight intent")
    for index in (5,9)
        J._direct_refactorize_with_exporter!(ordinary,f.matrices[index],reference_exporter)
        J._bgx_refactor_with!(candidate,f.matrices[index];export_parts=exporter)
        require(candidate.inner.base.pivot_policy===policy(backend),"Refactor intent")
        require(J._direct_mode(ordinary)==J._direct_mode(candidate),"Preflight paired modes")
    push!(modes,string(J._direct_mode(candidate)))
    end
    require(length(refs)==length(cands)==length(modes)==3 && unchanged(f,source),"Preflight completeness/inputs")
    return Dict("reference"=>refs,"candidate"=>cands,"modes"=>modes,"inputs_unchanged"=>true,
        "constructions"=>2,"refactors"=>4,"explicit_solves"=>0)
end
# All definitions are loaded before main, avoiding the prior include/global-binding warning.
function main()
    completed=false;fatal="";cells=0;windows=0;loaded=Dict{String,String}()
    try
        require(PHASE in ("cost1-300","cost2-300","cost1-600","cost2-600"),"Unexpected phase")
        require(realpath(pathof(J))==realpath(joinpath(PROJECT,"src","JSimplex.jl")),"Wrong loaded module")
        require(Threads.nthreads()==1 && BLAS.get_num_threads()==1 && !PrecompileTools.verbose[],"Thread/precompile configuration")
        loaded=Dict(string(nameof(m))=>realpath(pathof(m)) for m in (J,LinearAlgebra,SparseArrays,TOML,PrecompileTools))
        println(stderr,"BEGIN BG export workspace cost ",PHASE);flush(stderr)
        source=TOML.parsefile(joinpath(@__DIR__,"inputs.toml"))["fixtures"]
        save("controls.toml",bounded_controls([decode_fixture(input) for input in source]))
        for input in source
            f=decode_fixture(input);outputs=[zeros(f.n) for _ in 1:24]
            for (label,F) in (("BG",J.BartelsGolubFactorization),), backend in (:native,:markowitz)
                cell=cells+1;identity=Dict("fixture"=>f.name,"manager"=>label,"backend"=>string(backend),"policy"=>policy_name(Val(backend)))
                save("started-$cell.toml",identity)
                save("preflight-$cell.toml",preflight(F,Val(backend),f,input))
                save("probe-$cell.toml",probe(Val(backend),f,input))
                for pair in 1:10
                    reference_first=isodd(pair) ⊻ startswith(PHASE,"cost2")
                    sides=reference_first ? (Val(:reference),Val(:candidate)) : (Val(:candidate),Val(:reference))
                    for (order,side) in enumerate(sides)
                        row=window(F,Val(backend),side,f,input,pair,order,outputs);windows+=1
                        save("window-$cell-$(2*(pair-1)+order).toml",row)
                        require(row["correct"],"Correctness/mode/input failure; stop")
                        require(!row["measured"] || (row["compile_seconds"]==0 && row["recompile_seconds"]==0),"Measured compilation; stop")
                        row=nothing # no unused per-cell result retention
                    end
                end
                save("cell-$cell.toml",merge(identity,Dict("windows"=>20)))
                cells+=1
            end
        end
        completed=true
    catch e
        fatal=sprint(showerror,e,catch_backtrace());println(stderr,"FATAL COST: ",fatal);flush(stderr)
    finally
        save("raw.toml",Dict("phase"=>PHASE,"loaded"=>loaded,"completed"=>completed,"fatal"=>fatal,
            "cells"=>cells,"windows"=>windows,"threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads()))
    end
    completed || exit(2)
end
main()
