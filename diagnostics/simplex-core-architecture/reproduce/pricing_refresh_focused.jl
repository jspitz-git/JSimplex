using JSimplex, Test, TOML, SHA, LinearAlgebra
const ROOT=dirname(dirname(pathof(JSimplex)))
include(joinpath(ROOT,"test/legacy_primal_preference_work_tests.jl"))
@assert !ispath(only(ARGS))
open(only(ARGS),"w") do io
 TOML.print(io,Dict("source"=>pathof(JSimplex),"complete"=>true,
     "test_source_sha256"=>bytes2hex(sha256(read(joinpath(ROOT,"test/legacy_primal_preference_work_tests.jl")))),
     "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads()))
end
