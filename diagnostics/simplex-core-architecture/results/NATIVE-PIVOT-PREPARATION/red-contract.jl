# UNEXECUTED. Only missing interface markers, no native/factor/solver calls.
using Test, JSimplex
@testset "Missing native pivot policy contract" begin
    @test hasfield(SolverOptions{Float64,:pfi,:native}, :native_pivot_policy)
    @test isdefined(JSimplex, :_NativePivotPolicy)
    @test hasfield(JSimplex.UMFPACKBackend, :pivot_policy)
    @test isdefined(JSimplex, :_native_lu)
end
