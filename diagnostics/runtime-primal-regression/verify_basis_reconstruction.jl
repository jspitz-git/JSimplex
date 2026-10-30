# Verify the saved published basis state, without advancing simplex iterations.
# julia --project=. verify_basis_reconstruction.jl snapshot.bin report.toml [baseline]
using JSimplex, Serialization, LinearAlgebra, Statistics, SHA, TOML
const JS=JSimplex

function restore_reconstruction_workspace(d)
    progress=JS.SimplexProgressContext(d.problem;numerical_policy=d.policy)
    ws=JS.initialize_workspace(d.problem,d.options;progress)
    ws.basis=JS.Basis(copy(d.basis.basic_indices),copy(d.basis.states))
    ws.primal.=d.primal;ws.costs.=d.costs;ws.lower.=d.lower;ws.upper.=d.upper
    ws.scratch.rho.=d.rho;ws.reduced_costs.=d.reduced_costs
    ws.iterations=d.iterations;ws.refactorizations=d.refactorizations
    ws.perturbed=d.perturbed
    ws.factorization=deepcopy(d.factorization)
    return ws
end

function reconstruction_quality(ws)
    B=JS.basis_matrix(ws)
    scratch=JS.SolveQualityScratch(eltype(ws.primal),length(ws.basis.basic_indices))
    primal=JS.solve_quality!(scratch,B,ws.primal[ws.basis.basic_indices],
        JS._basis_primal_rhs(ws),ws.progress.numerical_policy)
    dual=JS.solve_quality!(scratch,B,ws.scratch.rho,ws.costs[ws.basis.basic_indices],
        ws.progress.numerical_policy;transposed=true)
    return Dict("primal_reliable"=>primal.reliable,"transpose_reliable"=>dual.reliable,
        "primal_relative_error"=>primal.relative_error,
        "transpose_relative_error"=>dual.relative_error)
end

function verify_reconstruction(input,output;baseline=false)
    ispath(output) && error("Use a fresh output path: "*output)
    d=deserialize(input)
    ws=restore_reconstruction_workspace(d)
    before=reconstruction_quality(ws)
    stop=()->false
    # Warm compilation separately; every measured recovery starts from the
    # saved primal/dual vectors, never from a previously corrected point.
    warm=@timed JS._try_native_cleanup_recompute!(ws,stop)
    samples=Dict{String,Any}[]
    for _ in 1:3
        ws.primal.=d.primal;ws.scratch.rho.=d.rho;ws.reduced_costs.=d.reduced_costs
        t=@timed JS._try_native_cleanup_recompute!(ws,stop)
        push!(samples,Dict("accepted"=>t.value,"seconds"=>t.time,"bytes"=>t.bytes,
            "compile_seconds"=>t.compile_time,
            "allocations"=>Base.gc_alloc_count(t.gcstats)))
    end
    after=reconstruction_quality(ws)
    # Exercise the real driver verification, including its initial recompute.
    restored=restore_reconstruction_workspace(d)
    driver=JS._verify_driver_basis!(restored,stop)
    driver_quality=reconstruction_quality(restored)
    unchanged=all(w.options===d.options && w.progress.numerical_policy===d.policy &&
        w.costs==d.costs && w.lower==d.lower && w.upper==d.upper &&
        w.basis.basic_indices==d.basis.basic_indices && w.basis.states==d.basis.states &&
        w.iterations==d.iterations for w in (ws,restored))
    success=all(s["accepted"] for s in samples) && after["primal_reliable"] &&
        after["transpose_reliable"] && driver && driver_quality["primal_reliable"] &&
        driver_quality["transpose_reliable"] && unchanged
    report=Dict("success"=>success,"baseline_mode"=>baseline,"before"=>before,
        "after"=>after,"driver_verified"=>driver,"driver_quality"=>driver_quality,
        "basis_costs_bounds_options_policy_iterations_unchanged"=>unchanged,
        "iterations"=>d.iterations,"julia"=>string(VERSION),"architecture"=>string(Sys.ARCH),
        "blas_threads"=>BLAS.get_num_threads(),"warmup_seconds"=>warm.time,
        "warmup_compile_seconds"=>warm.compile_time,"samples"=>samples,
        "median_recovery_seconds"=>median(s["seconds"] for s in samples),
        "samples_include_compilation"=>any(s["compile_seconds"]>0 for s in samples),
        "timing_note"=>"Recovery times include any residual compilation and GC; compilation is reported separately and does not determine numerical success.",
        "solve_tolerance"=>d.policy.solve_tolerance,
        "primal_tolerance"=>d.options.primal_tolerance,"dual_tolerance"=>d.options.dual_tolerance,
        "input_sha256"=>bytes2hex(open(sha256,input)),
        "source_sha256"=>Dict(f=>bytes2hex(open(sha256,joinpath(dirname(pathof(JS)),f)))
            for f in ("native_phase_transfer.jl","native_cleanup_recovery.jl","simplex_driver.jl")),
        "scope"=>"Basis reconstruction and real driver verification; no resumed LP optimization.")
    mkpath(dirname(abspath(output)))
    open(output,"w") do io;TOML.print(io,report;sorted=true);end
    println("Reconstruction verified: ",success,"; report: ",output)
    @assert unchanged
    @assert baseline ? !success : success
end

if abspath(PROGRAM_FILE)==@__FILE__
    length(ARGS) in (2,3) || error("Expected: snapshot.bin report.toml [baseline]")
    length(ARGS)==2 || ARGS[3]=="baseline" || error("Unknown verification mode")
    verify_reconstruction(ARGS[1],ARGS[2];baseline=length(ARGS)==3)
end
