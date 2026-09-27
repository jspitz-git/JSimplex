using TOML, SHA, LinearAlgebra
BLAS.set_num_threads(1)
const cold_algorithm = Symbol(ARGS[1])
const cold_output = ARGS[2]
load_stats = @timed @eval using JSimplex
setup_stats = @timed @eval begin
    const cold_problem = read_mps(joinpath(dirname(dirname(pathof(JSimplex))), "test/fixtures/solver/afiro.mps"))
    const cold_strategy = hasproperty(SolverOptions(), :simplex_strategy) ? (;simplex_strategy=:legacy) : (;)
    const cold_options = SolverOptions(;cold_strategy..., algorithm=cold_algorithm,
        pricing=:steepest_edge, basis_update=:bartels_golub, basis_refactorization=:native,
        refactorization_interval=80, iteration_limit=1_000_000, time_limit=60.0, verbose=false)
end
function timing_record(stats)
    Dict{String,Any}("seconds"=>stats.time, "compile_seconds"=>stats.compile_time,
         "recompile_seconds"=>stats.recompile_time, "gc_seconds"=>stats.gctime,
         "allocated_bytes"=>stats.bytes)
end
report=Dict{String,Any}("julia"=>string(VERSION), "machine"=>Sys.MACHINE,
    "cpu"=>Sys.CPU_NAME, "blas"=>string(BLAS.get_config()), "algorithm"=>string(cold_algorithm),
    "source"=>pathof(JSimplex), "load"=>timing_record(load_stats), "setup"=>timing_record(setup_stats),
    "samples"=>Dict{String,Any}[])
h=SHA.SHA2_256_CTX(); root=dirname(dirname(pathof(JSimplex)))
files=["Project.toml"]
for (dir,_,names) in walkdir(joinpath(root,"src")),name in names
    endswith(name,".jl") && push!(files,relpath(joinpath(dir,name),root))
end
for name in sort(files); SHA.update!(h,codeunits(name*"\0")); SHA.update!(h,read(joinpath(root,name))); end
report["production_sha256"]=bytes2hex(SHA.digest!(h))
for repetition in 1:3
    GC.gc()
    stats=@timed @eval solve(cold_problem; options=cold_options, relax_integrality=true)
    result=stats.value
    row=timing_record(stats)
    row["repetition"]=repetition;row["status"]=string(result.status)
    row["iterations"]=result.statistics.iterations
    row["refactorizations"]=result.statistics.refactorizations
    @assert result.status==OPTIMAL
    @assert isapprox(result.objective_value,-464.7531428571429;atol=1e-7,rtol=1e-8)
    @assert JSimplex._original_primal_feasible(cold_problem,result.primal,cold_options.primal_tolerance)
    row["objective"]=result.objective_value
    push!(report["samples"],row)
    open(cold_output,"w") do io; TOML.print(io,report); end
    println("SAMPLE ",row);flush(stdout)
end
