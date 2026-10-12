using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
const JS=JSimplex
const ROOT=dirname(dirname(pathof(JS)))
const FILE=joinpath(ROOT,"test/dual_pivot_consistency_tests.jl")
const SOURCE=read(FILE,String)
Base.include_string(@__MODULE__,first(split(SOURCE,"\n@testset")),FILE)
const TITLES=("Failed dual pivot recovery remains bounded and unpublished",
              "Cancellation after dual refresh cannot publish a pivot")
const NODES=filter(x->x isa Expr && x.head==:macrocall &&
    x.args[1]==Symbol("@testset") && any(t->t in x.args,TITLES),Meta.parseall(SOURCE).args)
@assert length(NODES)==2
const MODES=(:exhausted,:cancelled,:callback_error,:numerical_callback_error,:after_refresh)
const MANAGERS=(:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
function snapshot(ws)
    Dict("primal"=>copy(ws.primal),"costs"=>copy(ws.costs),"prices"=>copy(ws.reduced_costs),
        "states"=>string.(ws.basis.states),"basis"=>copy(ws.basis.basic_indices),
        "iterations"=>ws.iterations,"refactorizations"=>ws.refactorizations,
        "rejected_rows"=>copy(ws.scratch.rejected_rows),
        "rejected_entering"=>copy(ws.scratch.rejected_entering),
        "updates"=>length(ws.factorization.updates))
end
function fixture(manager,mode,diagnostics=nothing)
    mode==:after_refresh && return duplicate_dual_column_workspace(;manager,diagnostics)
    policy=JS.NumericalPolicy(Float64;max_pivot_candidates=mode==:cancelled ? 2 : 1,max_recovery_rounds=0)
    duplicate_dual_column_workspace(;manager,policy,diagnostics)
end
function observe(manager,mode;record=false)
    rejected=Ref(0);cancelled=Ref(false);events=String[]
    observer=(event,ws)->begin
        record && push!(events,string(event))
        if mode==:after_refresh
            event==:refactor_pivot && (cancelled[]=true)
        elseif event==:pivot_rejected
            rejected[]+=1
            mode==:cancelled && (cancelled[]=true)
            mode==:callback_error && error("rejected pivot observer")
            mode==:numerical_callback_error && throw(SingularException(7))
        end
        nothing
    end
    d=JS.SimplexDiagnostics(;observer)
    ws=fixture(manager,mode,d);before=snapshot(ws)
    result=try JS.dual_iteration!(ws,()->cancelled[]) catch e; e end
    after=snapshot(ws)
    Dict("manager"=>string(manager),"mode"=>string(mode),"before"=>before,"after"=>after,
        "result_type"=>string(typeof(result)),
        "status"=>result isa JS.DualTermination ? string(result.status) : "none",
        "message"=>result isa JS.DualTermination ? result.message : result isa Exception ? sprint(showerror,result) : "nothing",
        "wrapped_cause"=>result isa JS.DiagnosticObserverFailure ? string(typeof(result.cause)) : "none",
        "rejected"=>rejected[],"cancelled"=>cancelled[],"events"=>events,
        "counts"=>Dict(string(k)=>v for (k,v) in d.counts),
        "numerical_state_unchanged"=>all(isequal(before[k],after[k]) for k in ("primal","costs","prices","states","basis","iterations")),
        "selected_row"=>ws.scratch.selected_row,"selected_entering"=>ws.scratch.selected_entering,
        "policy"=>Dict("max_pivot_candidates"=>ws.progress.numerical_policy.max_pivot_candidates,
                       "max_recovery_rounds"=>ws.progress.numerical_policy.max_recovery_rounds,
                       "max_refinements"=>ws.progress.numerical_policy.max_refinements))
end
function probe(manager,mode)
    # Fresh independent fixture after the two attempts: these scratch writes
    # cannot affect the paired production iterations or their original oracle.
    ws=fixture(manager,mode);row=JS.dual_edge_selection(ws)
    @assert row>0
    j=ws.basis.basic_indices[row]
    below=JS._lower_violation(ws.lower[j],ws.primal[j])>0
    bound=below ? ws.lower[j] : ws.upper[j]
    delta=ws.primal[j]-JS.bound_value(bound)
    unit=JS._pipeline_unit_rhs!(ws,row)
    rho=JS._pipeline_basis_solve!(ws.scratch.rho,ws,unit;transposed=true,unit_row=row)
    tableau=ws.scratch.tableau_row;JS.price!(tableau,ws,rho)
    ratio=JS._dual_row_residual_ratio(ws,rho,row)
    entering,flips,exhausted=JS._configured_dual_ratio_test(ws,tableau,below ? -1.0 : 1.0,abs(delta))
    out=Dict{String,Any}("row"=>row,"entering"=>entering,"exhausted"=>exhausted,
       "rho"=>copy(rho),"tableau"=>copy(tableau),"row_residual_ratio"=>ratio,
       "flip_count"=>length(flips),"native_refactor"=>string(ws.options.basis_refactorization))
    if entering>0
        column=JS._pipeline_column_rhs!(ws,entering)
        direction=JS._pipeline_basis_solve!(ws.scratch.row_solution,ws,column;prepare_update=true)
        pivot=direction[row];rowpivot=tableau[entering]
        out["direction"]=copy(direction);out["pivot"]=pivot;out["row_pivot"]=rowpivot
        out["direction_residual_ok"]=JS._dual_direction_residual_ok!(ws,direction,pivot)
        out["pivot_agrees"]=JS._pivot_agrees(rowpivot,pivot,sqrt(eps(Float64))*max(abs(pivot),abs(rowpivot)))
    end
    return out
end
records=Dict[]
@testset "Dual recovery observer census" begin
    for manager in MANAGERS,mode in MODES
        control=observe(manager,mode)
        observed=observe(manager,mode;record=true)
        equal=all(isequal(control[k],observed[k]) for k in keys(control) if k!="events")
        @test equal
        push!(records,Dict("control"=>control,"observed"=>observed,"equal"=>equal,
                          "probe"=>probe(manager,mode)))
    end
end
@assert !ispath(only(ARGS))
open(only(ARGS),"w") do io
    TOML.print(io,Dict("source"=>pathof(JS),"test_sha256"=>bytes2hex(sha256(SOURCE)),
      "julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH),
      "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),"records"=>records))
end
# Original AST nodes are never rewritten. An enclosing testset runs both even
# if one oracle reports failures, preserving every original assertion.
@testset "Original dual recovery oracles" begin
    for node in NODES
        Core.eval(@__MODULE__,node)
    end
end
