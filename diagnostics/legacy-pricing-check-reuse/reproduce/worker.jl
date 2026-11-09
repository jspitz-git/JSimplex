include("common.jl")
arm in ("candidate","shadow") && include("candidate.jl")
if auditing
    include("audit.jl")
else
    install_method("_dual_optimize!";transform=time_loop)
end
function persist(path,d)
    open(io->TOML.print(io,d),path,"w")
end
function run()
    @assert Threads.nthreads()==BLAS.get_num_threads()==1 && Sys.ARCH==:aarch64
    lp=read_mps(input)
    model_sha=bytes2hex(open(sha256,input))
    expected = realpath(input)==realpath(joinpath(@__DIR__,"afiro.mps")) ?
        bytes2hex(open(sha256,joinpath(@__DIR__,"afiro.mps"))) :
        "d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68"
    @assert model_sha==expected
    for (name,p,limit) in (("afiro",read_mps(joinpath(@__DIR__,"afiro.mps")),typemax(Int)),("input",lp,100))
        r=solve(p;options=opts(limit),relax_integrality=true)
        if !(r.status==OPTIMAL || (name=="input" && r.status==ITERATION_LIMIT))
            persist(output*".warmup-failure.toml",Dict("stage"=>name,"status"=>string(r.status),
                "message"=>r.message,"iterations"=>r.statistics.iterations))
            return
        end
        if name=="afiro"
            @assert JS._original_primal_feasible(p,r.primal,1e-7)
        end
    end
    reset_measurement!()
    if auditing
        reset_audit!();empty!(pricing_counts);empty!(switch_history)
    end
    GC.gc()
    measured_start=time()
    t=@timed solve(lp;options=opts(typemax(Int)),relax_integrality=true)
    measured_end=time()
    r=t.value
    d=Dict("profile"=>profile,"pricing"=>pricing_arg,"arm"=>arm,"status"=>string(r.status),"message"=>r.message,
        "original_feasible"=>r.status==OPTIMAL && JS._original_primal_feasible(lp,r.primal,1e-7),
        "objective_bits"=>isnothing(r.objective_value) ? "" : string(reinterpret(UInt64,r.objective_value),base=16),
        "primal_sha"=>isnothing(r.primal) ? "" : bytes2hex(sha256(reinterpret(UInt8,r.primal))),
        "iterations"=>r.statistics.iterations,"refactors"=>r.statistics.refactorizations,"mode_initial"=>initial_count[],
        "mode_refactors"=>refactor_count[],"mode"=>representation,"loop"=>loop_ns[]/1e9,"steps"=>loop_steps[],"entries"=>loop_entries[],
        "seconds"=>t.time,"measured_start"=>measured_start,"measured_end"=>measured_end,"bytes"=>t.bytes,"allocations"=>Base.gc_alloc_count(t.gcstats),
        "gc"=>t.gctime,"compile"=>t.compile_time,"peak_rss_bytes"=>Sys.maxrss(),"threads"=>Threads.nthreads(),
        "blas_threads"=>BLAS.get_num_threads(),"arch"=>string(Sys.ARCH),"options"=>string(opts(typemax(Int))),"input_sha"=>model_sha)
    persist(output,d)
    if auditing
        a=audit_report()
        a["modes"]=mode_history
        a["pricing_counts"]=pricing_counts
        a["switches"]=switch_history
        persist(output*".audit.toml",a)
    end
    @assert loop_depth[]==0 && weight_context_ok()
end
weight_context_ok() = !auditing || weight_context[]==0
try
    run()
catch e
    persist(output*".exception.toml",Dict("exception"=>sprint(showerror,e,catch_backtrace())))
    if auditing && !isfile(output*".audit.toml")
        try
            partial=audit_report()
            partial["modes"]=mode_history
            partial["pricing_counts"]=pricing_counts
            partial["switches"]=switch_history
            persist(output*".partial-audit.toml",partial)
        catch salvage
            persist(output*".salvage-error.toml",Dict("exception"=>sprint(showerror,salvage)))
        end
    end
    rethrow()
end
