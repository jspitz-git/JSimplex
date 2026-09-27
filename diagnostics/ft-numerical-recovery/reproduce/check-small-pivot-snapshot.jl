# Check the isolated entering-price correction against the Windows 45538 state.
# This reconstructs the scalar entering price from the recorded outgoing price;
# it is not a complete restart or a replay of subsequent ratio decisions.
using JSimplex, Serialization, LinearAlgebra, TOML, Test
function check_snapshot(report_path, snapshot_path)
    report = TOML.parsefile(report_path)
    data = deserialize(snapshot_path)
    for key in (:run_id, :source_revision, :input_sha256, :julia, :architecture)
        @assert getproperty(data,key) == report[string(key)]
    end
    @assert data.iteration == 45538 && hasproperty(data,:prior_basis)
    ws = JSimplex.initialize_workspace(data.problem,data.options)
    ws.basis = deepcopy(data.prior_basis)
    ws.costs .= data.costs; ws.lower .= data.lower; ws.upper .= data.upper
    ws.perturbed = data.perturbed
    B = JSimplex.basis_matrix(ws); factor = lu(B)
    low = JSimplex._refined_dual_prices(ws,factor,B,256,()->false)
    high = JSimplex._refined_dual_prices(ws,factor,B,512,()->false)
    @assert !isnothing(low) && !isnothing(high)
    entering = data.entering
    leaving = ws.basis.basic_indices[data.row]
    coefficient = data.tableau[entering]
    old_price = -data.prices[leaving] * coefficient
    ws.reduced_costs .= Float64.(high)
    ws.reduced_costs[ws.basis.basic_indices] .= 0.0
    ws.reduced_costs[entering] = old_price
    expected = high[entering]
    rhs = copy(JSimplex._pipeline_column_rhs!(ws,entering))
    direction = JSimplex._refined_primal_direction(factor,B,rhs,256,()->false)
    @assert !isnothing(direction)
    outgoing_reference = -expected / direction[data.row]
    error_before = Float64(abs(BigFloat(old_price)-expected)/abs(BigFloat(coefficient)))
    old_costs = copy(ws.costs)
    @testset "Captured Windows forward-price correction" begin
        @test abs(low[entering]-expected) < big"1e-30"
        @test error_before > ws.options.dual_tolerance
        @test JSimplex._stabilize_small_dual_pivot!(ws,entering,data.direction[data.row],
            coefficient,data.last_step*data.direction[data.row],()->false)
        @test ws.costs == old_costs
        error_after = Float64(abs(BigFloat(ws.reduced_costs[entering])-expected)/abs(BigFloat(coefficient)))
        @test error_after < 1e-12
        outgoing_error_before = Float64(abs(BigFloat(data.prices[leaving])-outgoing_reference))
        outgoing_error_after = Float64(abs(BigFloat(-ws.reduced_costs[entering]/coefficient)-outgoing_reference))
        @test outgoing_error_before > ws.options.dual_tolerance
        @test outgoing_error_after < ws.options.dual_tolerance
        println("PRICE old=",old_price," certified=",Float64(expected),
            " replacement=",ws.reduced_costs[entering],
            " amplified_error_before=",error_before," amplified_error_after=",error_after,
            " outgoing_error_before=",outgoing_error_before," outgoing_error_after=",outgoing_error_after)
    end
end
Base.invokelatest(check_snapshot,ARGS...)
