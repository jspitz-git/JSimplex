# Verify the detached fresh-run export without replacing production methods.
using JSimplex, Serialization, LinearAlgebra, SHA, TOML, Test
BLAS.set_num_threads(1)
length(ARGS)==2 || error("Expected snapshot output-prefix")
snapshot,output=ARGS
function load_workspace()
    ws=deserialize(snapshot);p=ws.progress
    ws.progress=JSimplex.SimplexProgressContext(ws.problem;start_ns=time_ns(),scaling=p.scaling,
        iteration_offset=p.iteration_offset,refactorization_offset=p.refactorization_offset,
        numerical_policy=p.numerical_policy)
    journal=ws.scratch.perturbations
    isnothing(journal) || (journal.workspace_id=objectid(ws))
    ws
end
function qualities(ws)
    B=JSimplex._basis_matrix!(ws);rhs=JSimplex._basis_primal_rhs(ws)
    policy=ws.progress.numerical_policy
    result=Dict{String,Any}()
    for (name,x,b,transposed) in (("primal",ws.primal[ws.basis.basic_indices],rhs,false),
        ("dual",ws.scratch.rho,ws.costs[ws.basis.basic_indices],true))
        s=JSimplex.SolveQualityScratch(Float64,length(b))
        q=JSimplex._compensated_solve_quality!(s,B,x,b,policy,transposed)
        @assert !isnothing(q)
        bad=findall(i->abs(s.residual[i])>policy.solve_tolerance*s.work_scale[i],eachindex(b))
        result[name]=Dict("reliable"=>q.reliable,"absolute_error"=>q.absolute_error,
            "relative_error"=>q.relative_error,"bad_rows"=>bad)
    end
    result
end
report=Dict{String,Any}("snapshot_sha256"=>bytes2hex(open(sha256,snapshot)),
    "scope"=>"Detached export replay with a new clock; no outer-driver continuation")
@testset "Fresh runtime export component recovery" begin
    ws=load_workspace();before=copy(ws.primal)
    report["before"]=qualities(ws)
    @test !report["before"]["primal"]["reliable"]
    @test JSimplex._complete_native_phase_transfer!(ws,()->false)
    report["after"]=qualities(ws)
    @test report["after"]["primal"]["reliable"]
    @test report["after"]["dual"]["reliable"]
    @test JSimplex._recomputed_basis_reliable(ws)
    @test JSimplex._legacy_primal_point_certified(ws)
    @test JSimplex._start_primal_feasible(ws)
    @test JSimplex._original_primal_feasible(ws,ws.primal[1:size(ws.problem.A,2)])
    nonbasic=ws.basis.states.!=JSimplex.BASIC
    @test isequal(ws.primal[nonbasic],before[nonbasic])
    report["maximum_primal_change"]=maximum(abs,ws.primal-before)
    report["iteration"]=ws.iterations
    report["objective"]=dot(ws.costs,ws.primal)
    serialize(output*".bin",ws)
    for mode in (:budget,:certificate,:cancel,:exception)
        ws=load_workspace()
        if mode==:budget
            ws.progress=JSimplex.SimplexProgressContext(ws.problem;
                numerical_policy=JSimplex.NumericalPolicy(Float64;max_refinements=0))
        elseif mode==:certificate
            ws.upper[first(ws.basis.basic_indices)]=JSimplex.Bound(-1e99)
        end
        saved=deepcopy((ws.primal,ws.scratch.row_solution,ws.scratch.rho,ws.reduced_costs))
        hit=Ref(false);error=ErrorException("cancel after tentative export")
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
end
open(output*".toml","w") do io
    TOML.print(io,report)
end
