module DualRowAdapterOptionsTests
using Test, JSimplex
import MathOptInterface as MOI
@testset "Dual row adapter is an explicit opt-in" begin
    options = SolverOptions()
    @test hasproperty(options, :dual_row_adapter)
    if hasproperty(options, :dual_row_adapter)
        @test options.dual_row_adapter === false
        for T in (Float32, Float64, BigFloat, Rational{BigInt})
            enabled = SolverOptions(T; dual_row_adapter=true, verbose=false)
            @test enabled.dual_row_adapter
            @test SolverOptions(T, enabled).dual_row_adapter
            @test JSimplex._phase_options(enabled, :dual).dual_row_adapter
        end
    end
end

@testset "Option survives bounded, auxiliary and precision copies" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        o=SolverOptions(T;dual_row_adapter=true,verbose=false)
        @test JSimplex._remaining_options(o;iterations=1).dual_row_adapter
        @test JSimplex._copy_precision_options(T,o).dual_row_adapter
        @test JSimplex._lp_auxiliary_options(o,(iteration_limit=10,iterations=1,time_limit_seconds=Inf)).dual_row_adapter
        for n in (16,17,20)
            previous=typeof(o)(ntuple(i->getfield(o,i),n)...)
            @test !previous.dual_row_adapter
        end
        optimizer=JSimplex.Optimizer{T}()
        attr=MOI.RawOptimizerAttribute("dual_row_adapter")
        @test MOI.supports(optimizer,attr)
        @test !MOI.get(optimizer,attr)
        MOI.set(optimizer,attr,true)
        @test MOI.get(optimizer,attr)
        @test JSimplex._solver_options(optimizer).dual_row_adapter
        MOI.set(optimizer,MOI.RawOptimizerAttribute("partial_pricing"),true)
        @test MOI.get(optimizer,attr)
        @test_throws ArgumentError MOI.set(optimizer,attr,1)
    end
end
end
