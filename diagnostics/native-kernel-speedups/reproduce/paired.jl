using JSimplex, LinearAlgebra, SHA, TOML, Serialization, Logging
const JS=JSimplex
const ROOT=dirname(dirname(pathof(JS)))
function main(case,out)
    ispath(out) && error("Choose a fresh output")
    @assert Threads.nthreads()==BLAS.get_num_threads()==1
    trace=SHA.SHA2_256_CTX();pivots=Ref(0)
    observer=(reason,ws)->begin
        if reason==:pivot_completed
            pivots[]+=1
            for values in (ws.basis.basic_indices,ws.primal,ws.reduced_costs,ws.pricing_weights)
                SHA.update!(trace,reinterpret(UInt8,values))
            end
        end
        nothing
    end
    diag=JS.SimplexDiagnostics(;observer)
    if case=="cleanup"
        input="/home/jspitz/.codex/worktrees/simplex-certificate-repair/JSimplex.jl/.superpowers/certificate-repair/medium-primal-handoff.bin"
        expected="242d37ae60aa4a0d0f4768000024da8623b7c3d94d47f0c01d24eccbfba5a8cc"
        @assert bytes2hex(open(sha256,input))==expected
        d=deserialize(input);p=d.problem
        limit=d.iterations+640
        options=JS._remaining_options(d.options;iterations=d.options.iteration_limit-limit,time_limit=Inf)
    else
        @assert case in ("runtime","medium")
        input="/home/jspitz/mps/"*case*".mps"
        expected=case=="runtime" ? "d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68" : "79c374a584b1463305cf4b0faee8920d0364df2dd5d0468a44ab58d9e9d49dc0"
        @assert bytes2hex(open(sha256,input))==expected
        p=read_mps(input)
        options=SolverOptions(algorithm=case=="runtime" ? :dual : :primal,basis_update=:huangfu_hall,
            basis_refactorization=:native,refactorization_interval=320,pricing=:steepest_edge,
            simplex_strategy=:legacy,partial_pricing=false,time_limit=Inf,
            iteration_limit=case=="runtime" ? 1_000_000 : 2000,verbose=true)
    end
    warm=read_mps(joinpath(ROOT,"test/fixtures/solver/afiro.mps"))
    @assert with_logger(NullLogger()) do
        solve(warm;options,relax_integrality=true).status==OPTIMAL
    end
    GC.gc();println("MEASUREMENT_START ",case);flush(stdout)
    if case=="cleanup"
        ctx=JS.SolveContext(time_ns(),Inf,diag,JS.NumericalPolicy(Float64,options))
        t=@timed JS.cleanup_original(p,d.basis,options,ctx,d.iterations,d.refactorizations;target_primal=d.target_primal)
        r=t.value;iterations=r.iterations;status=r.status
    else
        t=@timed JS._solve_diagnosed(p,diag;options,relax_integrality=true)
        r=t.value;iterations=r.statistics.iterations;status=r.status
    end
    report=Dict{String,Any}("case"=>case,"status"=>string(status),"iterations"=>iterations,
        "pivot_events"=>pivots[],"trace_sha256"=>bytes2hex(SHA.digest!(trace)),
        "seconds"=>t.time,"compile_seconds"=>t.compile_time,"gc_seconds"=>t.gctime,"allocated_bytes"=>t.bytes,
        "input_sha256"=>expected,"algorithm"=>string(options.algorithm),"interval"=>options.refactorization_interval,
        "source_root"=>ROOT,"source_files"=>Dict(relpath(joinpath(dir,f),ROOT)=>bytes2hex(open(sha256,joinpath(dir,f))) for (dir,_,files) in walkdir(joinpath(ROOT,"src")) for f in files if endswith(f,".jl")),
        "events"=>Dict(string(k)=>v for (k,v) in diag.counts if v!=0))
    if status==OPTIMAL
        report["objective"]=case=="cleanup" ? JS._restored_objective(p,r.primal) : r.objective_value
        report["original_primal_feasible"]=JS._original_primal_feasible(p,r.primal,options.primal_tolerance)
        @assert report["original_primal_feasible"]
        case=="runtime" && @assert isapprox(r.objective_value,51425691.76210454;rtol=1e-8,atol=1e-7)
    end
    open(out,"w") do io;TOML.print(io,report);end
    @assert status==(case=="runtime" ? OPTIMAL : ITERATION_LIMIT)
    @assert case!="cleanup" || iterations==d.iterations+640
    println("MEASUREMENT_DONE ",case," ",status," iterations=",iterations);flush(stdout)
end
main(ARGS...)
