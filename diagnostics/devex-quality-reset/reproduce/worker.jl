include("common.jl")
include("policy.jl")
auditing && include("audit.jl")
install_method("_dual_optimize!";transform=time_loop)
const cert_calls=Ref(0);const cert_true=Ref(0);const cert_last=Ref(false)
install_method("_original_optimality_certified";transform=expr->begin
    body=expr.args[2]
    expr.args[2]=quote
        local value=(()->begin $body end)()
        Main.cert_calls[]+=1;Main.cert_true[]+=value;Main.cert_last[]=value
        return value
    end
    expr
end)
persist(path,d)=open(io->TOML.print(io,d),path,"w")
function run()
    @assert Threads.nthreads()==BLAS.get_num_threads()==1 && Sys.ARCH==:aarch64
    @assert mode in ("off","passive","active")
    model_sha=bytes2hex(open(sha256,input))
    expected = basename(input) in ("afiro.mps","sc50a.mps") ?
        bytes2hex(open(sha256,joinpath(@__DIR__,basename(input)))) :
        "d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68"
    @assert model_sha==expected
    lp=read_mps(input)
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
    reset_measurement!();reset_quality!()
    cert_calls[]=cert_true[]=0;cert_last[]=false
    auditing && (reset_audit!();reset_quality_audit!())
    GC.gc();start=time()
    t=@timed solve(lp;options=opts(typemax(Int)),relax_integrality=true)
    finish=time();r=t.value
    d=Dict("profile"=>profile,"pricing"=>pricing_arg,"arm"=>mode,"status"=>string(r.status),"message"=>r.message,
        "original_feasible"=>r.status==OPTIMAL && JS._original_primal_feasible(lp,r.primal,1e-7),
        "certificate_calls"=>cert_calls[],"certificate_true"=>cert_true[],"certificate_last"=>cert_last[],
        "objective"=>isnothing(r.objective_value) ? NaN : r.objective_value,
        "objective_bits"=>isnothing(r.objective_value) ? "" : string(reinterpret(UInt64,r.objective_value),base=16),
        "primal_sha"=>isnothing(r.primal) ? "" : bytes2hex(sha256(reinterpret(UInt8,r.primal))),
        "iterations"=>r.statistics.iterations,"refactors"=>r.statistics.refactorizations,
        "mode_initial"=>initial_count[],"mode_refactors"=>refactor_count[],"mode"=>representation,
        "loop"=>loop_ns[]/1e9,"steps"=>loop_steps[],"entries"=>loop_entries[],
        "seconds"=>t.time,"measured_start"=>start,"measured_end"=>finish,"bytes"=>t.bytes,
        "allocations"=>Base.gc_alloc_count(t.gcstats),"gc"=>t.gctime,"compile"=>t.compile_time,
        "peak_rss_bytes"=>Sys.maxrss(),"threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
        "arch"=>string(Sys.ARCH),"options"=>string(opts(typemax(Int))),"input_sha"=>model_sha,
        "quality_observed"=>mode!="off","quality_counts"=>quality_counts_report(),
        "state_payload_bytes"=>sizeof(QualityState),"weak_metadata_entries"=>length(quality_states))
    persist(output,d) # Numeric outcome survives subsequent metadata validation failure.
    auditing && persist(output*".audit.toml",detailed_audit())
    @assert loop_depth[]==0
end
try
    run()
catch e
    persist(output*".exception.toml",Dict("exception"=>sprint(showerror,e,catch_backtrace())))
    if auditing && !isfile(output*".audit.toml")
        try
            persist(output*".partial-audit.toml",detailed_audit())
        catch salvage
            persist(output*".salvage-error.toml",Dict("exception"=>sprint(showerror,salvage)))
        end
    end
    rethrow()
end
