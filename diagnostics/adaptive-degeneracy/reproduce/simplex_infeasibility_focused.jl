using JSimplex,Test,LinearAlgebra
BLAS.set_num_threads(1)
@testset "Simplex infeasibility tolerance and native regressions" begin
    root=dirname(dirname(pathof(JSimplex)))
    for name in ("simplex_infeasibility_tolerance","primal_simplex","dual_simplex","simplex_phase_one","simplex_phase_one_auxiliary")
        println("CHECK ",name);flush(stdout)
        include(joinpath(root,"test",name*"_tests.jl"))
    end
end
