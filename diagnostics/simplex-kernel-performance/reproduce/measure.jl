using JSimplex, Profile, Logging, TOML, SHA, Serialization, LinearAlgebra
const J = JSimplex
# Usage: measure.jl INPUT ALGORITHM ITERATIONS SECONDS OUTPUT [profile|trace]
function measure(input, algorithm, iterations, seconds, output, mode="trace"; manager=:pfi, strategy=:legacy)
    ispath(output*".toml") && error("Output already exists")
    options = SolverOptions(algorithm=Symbol(algorithm), pricing=:steepest_edge,
        basis_update=manager, basis_refactorization=:native, refactorization_interval=80,
        simplex_strategy=strategy, iteration_limit=parse(Int, iterations),
        time_limit=parse(Float64, seconds), verbose=false)
    p = read_mps(input)
    with_logger(NullLogger()) do
        solve(read_mps("test/fixtures/solver/afiro.mps");options,relax_integrality=true)
    end
    trace = IOBuffer()
    checkpoints = SHA.SHA2_256_CTX()
    latest = Ref{Any}(nothing)
    function checkpoint(ws)
        # Array storage is hashed verbatim, including signed zeros.
        for x in (ws.basis.basic_indices,ws.basis.states,ws.primal,ws.reduced_costs,
                  ws.costs,ws.pricing_weights)
            SHA.update!(checkpoints,reinterpret(UInt8,x))
        end
    end
    function observer(event,ws)
        latest[]=ws
        if event in (:pivot_completed,:flip_completed)
            write(trace,Int(ws.progress.iteration_offset),ws.iterations,
                ws.scratch.selected_row,ws.scratch.selected_entering,
                ws.scratch.last_primal_step,ws.scratch.last_dual_step)
            ws.iterations % 80 == 0 && checkpoint(ws)
        end
    end
    diagnostics = J.SimplexDiagnostics(;observer=mode=="trace" ? observer : nothing)
    run() = with_logger(NullLogger()) do
        J._solve_diagnosed(p,diagnostics;options,relax_integrality=true)
    end
    GC.gc()
    if mode=="profile"
        Profile.clear(); Profile.init(n=10_000_000,delay=0.005)
    end
    measured = mode=="profile" ? (@timed @profile run()) : (@timed run())
    r = measured.value
    if mode=="profile"
        open(output*".profile","w") do io
            Profile.print(io;format=:flat,sortedby=:count,mincount=10,C=false)
        end
    end
    isnothing(latest[]) || checkpoint(latest[])
    report = Dict("input"=>input,"input_sha256"=>bytes2hex(open(sha256,input)),
        "algorithm"=>algorithm,"manager"=>string(manager),"strategy"=>string(strategy),"mode"=>mode,"status"=>string(r.status),"message"=>r.message,
        "seconds"=>measured.time,"bytes"=>measured.bytes,"gc_seconds"=>measured.gctime,
        "compile_seconds"=>measured.compile_time,"iterations"=>r.statistics.iterations,
        "refactorizations"=>r.statistics.refactorizations,
        "objective"=>something(r.objective_value,NaN),
        "trace_sha256"=>bytes2hex(sha256(take!(trace))),
        "checkpoints_sha256"=>bytes2hex(SHA.digest!(checkpoints)),
        "counts"=>Dict(string(k)=>v for (k,v) in diagnostics.counts),
        "compile_mode"=>Int(Base.JLOptions().compile_enabled),"julia"=>string(VERSION),"architecture"=>string(Sys.ARCH),
        "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
        "source_sha256"=>Dict(f=>bytes2hex(open(sha256,joinpath("src",f))) for f in
            ("dual_simplex.jl","primal_simplex.jl","simplex.jl")))
    if r.status==OPTIMAL
        report["original_primal_certified"]=J._original_primal_feasible(p,r.primal,options.primal_tolerance)
        report["primal_sha256"]=bytes2hex(sha256(reinterpret(UInt8,r.primal)))
    end
    open(output*".toml","w") do io; TOML.print(io,report); end
    println(basename(input)," ",algorithm," ",manager," ",strategy," ",r.status," iterations=",r.statistics.iterations," seconds=",measured.time);flush(stdout)
end
abspath(PROGRAM_FILE) == (@__FILE__) && measure(ARGS...)
