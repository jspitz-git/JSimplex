using Test,JSimplex
@testset "Point certificate regression coverage" begin
 names=only(ARGS)=="allocation" ? ("primal_certificate_work_tests.jl","exact_primal_rows_tests.jl","primal_point_storage_tests.jl") :
  ("legacy_primal_point_tests.jl","legacy_primal_point_recovery_tests.jl","legacy_primal_perturbed_point_tests.jl","legacy_primal_balanced_point_tests.jl","legacy_primal_joint_point_tests.jl","legacy_primal_equation_point_tests.jl")
 for name in names
  println("TEST ",name);flush(stdout)
  path=joinpath(dirname(dirname(pathof(JSimplex))),"test",name)
  isfile(path) || error("Missing expected test file: "*name)
  include(path)
 end
end
