using JSimplex, LinearAlgebra, SHA, TOML, Logging
length(ARGS)==7 || error("Expected: input algorithm manager mode seconds iterations output")
const INPUT=ARGS[1]
const ALGORITHM=ARGS[2]
const MANAGER=ARGS[3]
const MODE=ARGS[4]
const SECONDS=ARGS[5]
const ITERATIONS=ARGS[6]
const OUTPUT=ARGS[7]
MODE in ("correction","direct","normalized") || error("Unknown mode")
if MODE!="correction"
    Base.include(JSimplex,joinpath(@__DIR__,"direct.jl"))
    Base.invokelatest(() -> JSimplex._install_trial_direct!(normalize=MODE=="normalized"))
end
function main()
    path=realpath(INPUT)
    lowercase(basename(path)) in ("big.mps","largo.mps","anymod.mps") && error("Excluded model")
    any(ispath,(OUTPUT,OUTPUT*".environment.toml")) && error("Choose a fresh output path")
    metadata=Dict{String,Any}("input"=>basename(path),"input_sha256"=>bytes2hex(open(sha256,path)),
        "mode"=>MODE,"algorithm"=>ALGORITHM,"manager"=>MANAGER,"interval"=>80,"pricing"=>"steepest_edge",
        "strategy"=>"legacy","backend"=>"native","julia"=>string(VERSION),"architecture"=>string(Sys.ARCH),
        "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
        "time_limit"=>parse(Float64,SECONDS),"iteration_limit"=>parse(Int,ITERATIONS))
    metadata["source_sha256"]=Dict(name=>bytes2hex(open(sha256,joinpath(dirname(pathof(JSimplex)),name)))
        for name in ("triangular_factorization.jl","triangular_rows.jl","triangular_indices.jl","triangular_spikes.jl"))
    metadata["prototype_sha256"]=bytes2hex(open(sha256,joinpath(@__DIR__,"direct.jl")))
    metadata["warmup"]="afiro, same algorithm/manager/mode, refactorization interval 2"
    open(OUTPUT*".environment.toml","w") do io;TOML.print(io,metadata);end
    manifest=joinpath(@__DIR__,"..","..","basis-selective-preparation","reproduce","external-inputs.toml")
    warm_entry=first(TOML.parsefile(manifest)["cases"])
    @assert warm_entry["id"]=="netlib/afiro"
    @assert bytes2hex(open(sha256,warm_entry["path"]))==warm_entry["sha256"]
    warm=read_mps(warm_entry["path"])
    warm_options=SolverOptions(algorithm=Symbol(ALGORITHM),basis_update=Symbol(MANAGER),basis_refactorization=:native,
        simplex_strategy=:legacy,pricing=:steepest_edge,refactorization_interval=2,verbose=false)
    warm_result=with_logger(NullLogger()) do
        Base.invokelatest(solve,warm;options=warm_options,relax_integrality=true)
    end
    @assert warm_result.status==OPTIMAL
    problem=read_mps(path)
    options=SolverOptions(algorithm=Symbol(ALGORITHM),basis_update=Symbol(MANAGER),basis_refactorization=:native,
        simplex_strategy=:legacy,pricing=:steepest_edge,refactorization_interval=80,
        time_limit=parse(Float64,SECONDS),iteration_limit=parse(Int,ITERATIONS),verbose=true)
    result=Base.invokelatest(solve,problem;options,relax_integrality=true)
    metadata["status"]=string(result.status);metadata["message"]=result.message
    metadata["iterations"]=result.statistics.iterations;metadata["seconds"]=result.statistics.elapsed_seconds
    metadata["refactorizations"]=result.statistics.refactorizations
    if result.status==OPTIMAL
        metadata["objective"]=result.objective_value
        metadata["original_primal_certified"]=JSimplex._original_primal_feasible(problem,result.primal,options.primal_tolerance)
        if metadata["input_sha256"]=="d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68"
            metadata["reference_objective"]=51425691.76210457
            metadata["objective_matches"]=isapprox(result.objective_value,metadata["reference_objective"];rtol=1e-8)
        end
    end
    open(OUTPUT,"w") do io;TOML.print(io,metadata);end
    println("FINAL ",metadata);flush(stdout)
end
Base.invokelatest(main)
