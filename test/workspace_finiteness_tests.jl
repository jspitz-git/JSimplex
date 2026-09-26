using SparseArrays

@testset "Workspace validation catches invalid values across vector blocks" begin
    for T in (Float32,Float64), pricing in (:steepest_edge,:dantzig)
        ws = JSimplex.initialize_workspace(LinearProblem(spzeros(T,0,4097),zeros(T,4097)),
            SolverOptions(T;pricing,verbose=false))
        @test JSimplex._finite_workspace(ws)
        for name in (:primal,:reduced_costs,:costs), position in (1,2048,4097), value in (T(NaN),T(Inf),T(-Inf))
            values = getfield(ws,name)
            old = values[position]; values[position] = value
            @test !JSimplex._finite_workspace(ws)
            values[position] = old
        end
        for position in (1,2048,4097), value in (T(NaN),T(Inf),zero(T),-zero(T),-one(T))
            old = ws.pricing_weights[position]; ws.pricing_weights[position] = value
            @test JSimplex._finite_workspace(ws) == (pricing == :dantzig)
            ws.pricing_weights[position] = old
        end
        ws.primal .= -zero(T)
        ws.costs .= floatmax(T)
        @test JSimplex._finite_workspace(ws)
    end
end
