# Exercise the full dense pipeline, including creation of call-local metadata.
function unit_pipeline_bytes!(ws,p)
    @allocated begin
        rhs=JSimplex._pipeline_unit_rhs!(ws,p)
        JSimplex._checked_basis_solve!(ws.scratch.rho,ws,rhs;transposed=true,unit_row=p)
    end
end
@testset "Unit BTRAN metadata does not allocate" begin
    for T in (Float32,Float64),manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub,:huangfu_hall),
        backend in (:native,:markowitz)
        ws=unit_rhs_workspace(T,manager,backend)
        unit_pipeline_bytes!(ws,3);unit_pipeline_bytes!(ws,3)
        @test unit_pipeline_bytes!(ws,3)==0
    end
end
