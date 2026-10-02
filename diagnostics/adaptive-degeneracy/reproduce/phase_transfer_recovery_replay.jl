# Verify production export against the saved runtime boundary, with no overrides.
helper_path=joinpath(@__DIR__,"replay_phase_transfer.jl")
helper_source=read(helper_path,String)
Base.include_string(Main,first(split(helper_source,"\nrecords=Dict{String,Any}[]")),helper_path)
report=Dict{String,Any}()
@testset "Production runtime phase transfer" begin
    data=load_transfer()
    accepted=JSimplex.remove_artificials!(data.phase,data.mapping,data.original,data.policy,()->false)
    @test accepted
    report["accepted"]=accepted
    for mode in (:budget,:checked,:dual,:cancel,:exception,:certificate)
        ws,_,_=mapped_workspace(load_transfer();carry=true)
        if mode in (:budget,:checked)
            policy=mode==:budget ? JSimplex.NumericalPolicy(Float64;max_refinements=0) :
                JSimplex.NumericalPolicy(Float64;solve_refinement=true)
            ws.progress=JSimplex.SimplexProgressContext(ws.problem;numerical_policy=policy)
        elseif mode==:dual
            ws.options=JSimplex._phase_options(ws.options,:dual)
        elseif mode==:certificate
            ws.upper[first(ws.basis.basic_indices)]=JSimplex.Bound(-1e99)
        end
        saved=deepcopy((ws.primal,ws.scratch.row_solution,ws.scratch.rho,ws.reduced_costs))
        hit=Ref(false);error=ErrorException("cancel after tentative phase point")
        stop=()->begin
            if mode in (:cancel,:exception) && !isequal(ws.primal,saved[1])
                hit[]=true
                mode==:exception && throw(error)
                return true
            end
            false
        end
        result=try JSimplex._complete_native_phase_transfer!(ws,stop) catch e; e end
        @test result === (mode==:exception ? error : false)
        @test isequal(saved,(ws.primal,ws.scratch.row_solution,ws.scratch.rho,ws.reduced_costs))
        mode in (:cancel,:exception) && (@test hit[])
    end

    if accepted
        ws=data.original
        @test JSimplex._recomputed_basis_reliable(ws)
        @test JSimplex._legacy_primal_point_certified(ws)
        @test JSimplex._original_primal_feasible(ws,ws.primal[1:size(ws.problem.A,2)])
        @test JSimplex._effective_pricing(ws,:primal)==:steepest_edge
        report["point"]=point_report(ws,"production export")
        serialize(output*".bin",ws)
    end
end
open(output*".toml","w") do io
    TOML.print(io,report)
end
