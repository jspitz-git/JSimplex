using JSimplex,Test,SparseArrays,LinearAlgebra,TOML,SHA
const ROOT=dirname(dirname(pathof(JSimplex)))
const FILES=("restoration_alias_copy_tests.jl","cost_restore_allocation_tests.jl",
 "simplex_perturbation_tests.jl","simplex_perturbation_integration_tests.jl",
 "primal_perturbation_tests.jl","primal_perturbation_integration_tests.jl",
 "partial_pricing_tests.jl","partial_pricing_integration_tests.jl",
 "basis_recovery_tests.jl")
@testset "Restoration focused regressions" begin
 for file in FILES
   println("FILE ",file);flush(stdout)
   include(joinpath(ROOT,"test",file))
 end
end
@assert !ispath(only(ARGS))
open(only(ARGS),"w") do io
 TOML.print(io,Dict("files"=>collect(FILES),"complete"=>true,
 "source_sha256"=>bytes2hex(sha256(read(joinpath(ROOT,"src/simplex_perturbation.jl")))),
 "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads()))
end
