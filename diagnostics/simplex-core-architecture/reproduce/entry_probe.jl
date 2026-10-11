using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, Logging
const JS=JSimplex
include(joinpath(@__DIR__,"../../../test/simplex_state_validity_helpers.jl"))
# Diagnostic hooks live only in this dedicated process, never in the test suite.
@eval JS begin
    const _entry_finite_calls=Ref(0)
    const _entry_value_visits=Ref(0)
end
source=read(joinpath(dirname(pathof(JS)),"dual_simplex.jl"),String)
position=findfirst("function _finite_workspace(",source)
ex,_=Meta.parse(source,first(position));body=ex.args[2]
ex.args[2]=quote
    _entry_finite_calls[]+=1
    $body
end
Core.eval(JS,ex)
# Count lengths at the executed hardware-float scan itself: that implementation
# visits every element, even after invalid data. Short-circuited arrays contribute
# nothing. This measures actual vector visits, not a fixed multiplier per check.
position=findfirst("function _finite_values(values::Vector",source)
ex,_=Meta.parse(source,first(position));body=ex.args[2]
ex.args[2]=quote
    _entry_value_visits[]+=length(values)
    $body
end
Core.eval(JS,ex)
function probe(owned;pricing=:steepest_edge,auto_state=false,adaptive=false,repair=false)
    ws=state_validity_fixture(;pricing,policy=JS.NumericalPolicy(Float64;adaptive_pricing=adaptive,adaptive_stalling=false))
    repair && (ws.reduced_costs[1]=-1.0)
    auto_state && (ws.scratch.pricing=JS.PricingState(Float64))
    stop=owned && isdefined(JS,:_SolveDeadline) ? JS._SolveDeadline(time_ns(),Inf) : ()->false
    guard=JS._guard_stop_callback(stop)
    JS._entry_finite_calls[]=0;JS._entry_value_visits[]=0
    result=JS._dual_optimize!(ws,guard)
    return (;status=string(result.status),iterations=ws.iterations,calls=JS._entry_finite_calls[],visits=JS._entry_value_visits[],
             primal=copy(ws.primal),costs=copy(ws.costs),prices=copy(ws.reduced_costs),
             weights=copy(ws.pricing_weights),basis=copy(ws.basis.basic_indices))
end
function main(output)
    rows=Dict[]
    @testset "Lexical dual entry saves one full check per ordinary pivot" begin
        for pricing in (:steepest_edge,:devex,:dantzig)
            opaque=probe(false;pricing);owned=probe(true;pricing)
            @test owned.status==opaque.status=="OPTIMAL"
            @test owned.iterations==opaque.iterations==2
            @test owned.calls==opaque.calls-owned.iterations
            @test opaque.visits-owned.visits==owned.iterations*4*(pricing==:dantzig ? 3 : 4)
            for field in (:primal,:costs,:prices,:weights,:basis)
                @test getproperty(owned,field)==getproperty(opaque,field)
            end
            push!(rows,Dict("pricing"=>string(pricing),"opaque_calls"=>opaque.calls,
                           "owned_calls"=>owned.calls,"opaque_visits"=>opaque.visits,"owned_visits"=>owned.visits,"iterations"=>owned.iterations))
        end
        # Conservative exclusion even when adaptive preparation is a no-op.
        opaque=probe(false;adaptive=true);owned=probe(true;adaptive=true)
        @test owned.calls==opaque.calls
        @test owned.status==opaque.status=="OPTIMAL"
        # Successful price refinement invalidates the first entry proof.
        opaque=probe(false;repair=true);owned=probe(true;repair=true)
        @test owned.status==opaque.status=="OPTIMAL"
        @test owned.iterations==opaque.iterations==2
        @test owned.calls==opaque.calls-(owned.iterations-1)
        for field in (:primal,:costs,:prices,:weights,:basis)
            @test getproperty(owned,field)==getproperty(opaque,field)
        end
        for pricing in (:auto,:steepest_edge)
            opaque=probe(false;pricing,auto_state=true);owned=probe(true;pricing,auto_state=true)
            @test owned.calls==opaque.calls
            @test owned.status==opaque.status=="OPTIMAL"
        end
    end
    open(output,"w") do io;TOML.print(io,Dict("cases"=>rows));end
end
Base.invokelatest(main,ARGS[1])
