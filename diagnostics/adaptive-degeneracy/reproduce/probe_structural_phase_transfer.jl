# A portable transfer control, not a reconstruction of the runtime endpoint.
using JSimplex, SparseArrays, Test, SHA, TOML, LinearAlgebra
BLAS.set_num_threads(1)
root=dirname(dirname(pathof(JSimplex)))
fixture_path=joinpath(root,"test/legacy_primal_structural_value_tests.jl")
fixture=read(fixture_path,String)
i=first(findfirst("function structural_zero_step_workspace",fixture))
j=first(findnext("\n@testset",fixture,i))-1
Base.include_string(Main,fixture[i:j],fixture_path)
records=Dict{String,Any}[]
@testset "Portable structural point transfer control" begin
    for T in (Float32,Float64), sign in (-1,1), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        base=structural_zero_step_workspace(T,sign,manager)
        @test isnothing(JSimplex._primal_iteration!(base,()->false,base.options.dual_tolerance))
        p=base.problem
        # Add an exactly zero nonbasic artificial, leaving the certified
        # original structural/activity point and its basis unchanged.
        auxiliary=LinearProblem(hcat(p.A,sparse(reshape(T[1,0],2,1))),T[0,0,1];
            row_lower=p.row_lower,row_upper=p.row_upper,
            column_lower=vcat(p.column_lower,Bound(zero(T))),
            column_upper=vcat(p.column_upper,Bound{T}(nothing)))
        phase=JSimplex.initialize_workspace(auxiliary,base.options)
        map=JSimplex.PhaseOneMap([1,2,4,5],[1,2,0,3,4],[3])
        phase.basis=JSimplex.Basis(map.original_to_phase[base.basis.basic_indices],
            vcat(base.basis.states[1:2],JSimplex.AT_LOWER,base.basis.states[3:4]))
        phase.iterations=base.iterations
        phase.primal[map.original_to_phase].=base.primal
        JSimplex.recompute!(phase;refactorize=true)
        phase.primal[map.original_to_phase].=base.primal
        phase.primal[3]=zero(T)
        phase.scratch.row_solution.=phase.primal[phase.basis.basic_indices]
        @test JSimplex._legacy_primal_point_certified(phase)
        @test JSimplex._original_optimality_certified(phase,phase.primal[1:3])
        @test JSimplex._original_primal_feasible(p,base.primal[1:2],base.options.primal_tolerance)
        original=JSimplex.initialize_workspace(p,base.options)
        old_basis=copy(original.basis.basic_indices);old_point=copy(original.primal)
        removed=JSimplex.remove_artificials!(phase,map,original,phase.progress.numerical_policy,()->false)
        @test !removed
        @test original.basis.basic_indices==old_basis && isequal(original.primal,old_point)
        # Diagnostic-only alternative: carry the mapped point as well as its
        # basis, then call the existing bounded native point completion.
        fresh=JSimplex.initialize_workspace(p,base.options)
        JSimplex._phase_inherit_work!(fresh,phase)
        fresh.basis=JSimplex.Basis(map.phase_to_original[phase.basis.basic_indices],
            phase.basis.states[map.original_to_phase])
        mapped=copy(phase.primal[map.original_to_phase])
        fresh.primal.=mapped
        candidate=copy(mapped[fresh.basis.basic_indices])
        JSimplex.recompute!(fresh;refactorize=true)
        raw_feasible=JSimplex._start_primal_feasible(fresh)
        @test !raw_feasible
        @test fresh.primal[1]==mapped[1]
        terminal=JSimplex._finish_legacy_primal_point!(fresh,candidate,()->false)
        @test isnothing(terminal)
        @test JSimplex._legacy_primal_point_certified(fresh)
        @test JSimplex._original_primal_feasible(p,fresh.primal[1:2],fresh.options.primal_tolerance)
        @test isequal(fresh.primal,mapped)
        push!(records,Dict("precision"=>string(T),"sign"=>sign,"basis_update"=>string(manager),
            "baseline_transfer_accepted"=>removed,"mapped_nonbasic_only_feasible"=>raw_feasible,
            "mapped_point_completion_accepted"=>isnothing(terminal),"same_mapped_point"=>isequal(fresh.primal,mapped),
            "original_primal_certified"=>true,"artificial_value"=>0.0))
    end
end
open(only(ARGS),"w") do io
    TOML.print(io,Dict("scope"=>"Portable transfer control; runtime transfer point was not captured",
        "fixture_sha256"=>bytes2hex(sha256(fixture)),"records"=>records))
end
