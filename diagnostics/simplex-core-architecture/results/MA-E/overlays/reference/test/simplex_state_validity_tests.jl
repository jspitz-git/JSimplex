using Test, JSimplex, SparseArrays, LinearAlgebra, Logging

include("simplex_state_validity_helpers.jl")

@testset "Owned deadline preserves expiry and public callback validation" begin
    available=isdefined(JSimplex,:_SolveDeadline)
    @test available
    if available
        deadline=JSimplex._SolveDeadline(time_ns(),Inf)
        @test !deadline()
        expired=JSimplex._SolveDeadline(time_ns(),0.0)
        @test expired()
        # Expiry at the retained inner poll after a successful outer check.
        ws=state_validity_fixture()
        @test JSimplex._finite_workspace(ws)
        result=JSimplex._dual_iteration_entry!(ws,JSimplex._guard_stop_callback(expired),true,Val(true))
        @test result.status==TIME_LIMIT
        @test ws.iterations==0
        for T in (Float32,Float64,BigFloat,Rational{BigInt}), rows in (1,3)
            ws=state_validity_fixture(T;rows)
            result=JSimplex._dual_optimize!(ws,JSimplex._guard_stop_callback(deadline))
            @test result.status==OPTIMAL
            @test ws.primal[1:rows]==ones(T,rows)
            ws=state_validity_fixture(T;rows)
            result=JSimplex._dual_optimize!(ws,JSimplex._guard_stop_callback(expired))
            @test result.status==TIME_LIMIT
            @test ws.iterations==0
        end
    end
    # The second stop poll sits between outer validation and iteration entry.
    # A retained array alias can change without a workspace-field assignment.
    for T in (Float32,Float64,BigFloat), field in (:primal,:reduced_costs,:costs),
        bad in (T(NaN),T(Inf),T(-Inf)), rows in (1,3)
        ws=state_validity_fixture(T;rows)
        alias=getproperty(ws,field)
        polls=Ref(0)
        stop=JSimplex._guard_stop_callback(()->begin
            polls[]+=1
            polls[]==2 && (alias[end]=bad)
            false
        end)
        result=JSimplex._dual_optimize!(ws,stop)
        @test result.status==NUMERICAL_ERROR
        @test ws.iterations==0
        @test polls[]==2
    end
    # A callback may replace the checked array, not just mutate an old alias.
    for field in (:primal,:reduced_costs,:costs)
        ws=state_validity_fixture();polls=Ref(0)
        replacement=copy(getproperty(ws,field));replacement[end]=NaN
        stop=JSimplex._guard_stop_callback(()->begin
            polls[]+=1
            polls[]==2 && setproperty!(ws,field,replacement)
            false
        end)
        result=JSimplex._dual_optimize!(ws,stop)
        @test result.status==NUMERICAL_ERROR
        @test ws.iterations==0
        @test polls[]==2
    end
    for bad in (NaN,Inf,-1.0,0.0)
        ws=state_validity_fixture()
        alias=ws.pricing_weights;polls=Ref(0)
        stop=JSimplex._guard_stop_callback(()->begin
            polls[]+=1
            polls[]==2 && (alias[end]=bad)
            false
        end)
        result=with_logger(NullLogger()) do
            JSimplex._dual_optimize!(ws,stop)
        end
        @test result.status==OPTIMAL
        @test ws.dual_devex_fallback
        @test all(w->isfinite(w)&&w>0,ws.pricing_weights)
    end
    for failure in (ErrorException("caller"),SingularException(1),ZeroPivotException(1))
        ws=state_validity_fixture();polls=Ref(0)
        stop=JSimplex._guard_stop_callback(()->begin
            polls[]+=1
            polls[]==2 && throw(failure)
            false
        end)
        caught=try JSimplex._dual_optimize!(ws,stop) catch e; e end
        @test caught===failure
        @test ws.iterations==0
    end
end

@testset "Owned entry never carries validity across observer mutations" begin
    if isdefined(JSimplex,:_SolveDeadline)
        for field in (:primal,:reduced_costs,:costs)
            injected=Ref(false)
            diagnostics=JSimplex.SimplexDiagnostics(;observer=(event,ws)->begin
                if event==:pivot_completed && !injected[]
                    getproperty(ws,field)[1]=NaN
                    injected[]=true
                end
            end)
            ws=state_validity_fixture(;diagnostics)
            stop=JSimplex._guard_stop_callback(JSimplex._SolveDeadline(time_ns(),Inf))
            result=JSimplex._dual_optimize!(ws,stop)
            @test injected[]
            @test result.status==NUMERICAL_ERROR
            @test ws.iterations==1
        end
        # Standalone iteration has no enclosing validated interval.
        for field in (:primal,:reduced_costs,:costs)
            ws=state_validity_fixture()
            getproperty(ws,field)[end]=NaN
            result=JSimplex.dual_iteration!(ws,JSimplex._SolveDeadline(time_ns(),Inf))
            @test result.status==NUMERICAL_ERROR
            @test ws.iterations==0
        end
    end
end
