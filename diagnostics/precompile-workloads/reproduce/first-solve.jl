using TOML
loaded = @timed @eval using JSimplex, SparseArrays
samples = Dict{String,Any}[]
single = get(ARGS,2,"") == "--single"
for T in (single ? (Float64,) : (Float64,Float32)),
    algorithm in (single ? (:primal,) : (:primal,:dual)),
    update in (single ? (:pfi,) : (:pfi,:bartels_golub,:forrest_tomlin,:suhl_suhl))
    # Different coefficients from the intended precompile examples. Cache reuse
    # should depend on call signatures, not on the numerical input.
    problem=LinearProblem(sparse(T[1 1; -1 1]),T[1,3];row_lower=T[4,2],column_lower=T[0,1])
    options=SolverOptions(T;algorithm,basis_update=update,basis_refactorization=:native,
        pricing=:steepest_edge,simplex_strategy=:legacy,presolve=false,verbose=false)
    measured=@timed solve(problem;options)
    result=measured.value
    @assert result.status==OPTIMAL
    @assert isapprox(result.objective_value,T(10);rtol=T(1e-5))
    @assert JSimplex._original_primal_feasible(problem,result.primal,options.primal_tolerance)
    sample=Dict{String,Any}("type"=>string(T),"algorithm"=>string(algorithm),"update"=>string(update),
        "seconds"=>measured.time,"compile_seconds"=>measured.compile_time,
        "recompile_seconds"=>measured.recompile_time,"objective"=>Float64(result.objective_value),
        "iterations"=>result.statistics.iterations)
    push!(samples,sample);println(sample);flush(stdout)
    open(ARGS[1],"w") do io
        TOML.print(io,Dict("julia"=>string(VERSION),"source_revision"=>strip(read(`git rev-parse HEAD`,String)),
            "load_seconds"=>loaded.time,"samples"=>samples))
    end
end
