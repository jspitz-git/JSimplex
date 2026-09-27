using JSimplex, Logging, Serialization, TOML, SHA
using JSimplex.LinearAlgebra
function main()
    path, algorithm, update, seconds, output = ARGS[1:5]
    lowercase(basename(realpath(path))) in ("big.mps", "largo.mps", "anymod.mps") && error("Excluded large model")
    options=SolverOptions(algorithm=Symbol(algorithm),basis_update=Symbol(update),
        basis_refactorization=:native,pricing=:steepest_edge,simplex_strategy=:legacy,
        refactorization_interval=parse(Int,get(ENV,"JSIMPLEX_DEBUG_INTERVAL","80")),time_limit=parse(Float64,seconds),
        iteration_limit=parse(Int,get(ENV,"JSIMPLEX_DEBUG_ITERATIONS","1000000")),verbose=true)
    events=Dict{Symbol,Int}()
    warming=Ref(true)
    marginal_snapshots=Ref(0)
    trace_pivots=get(ENV,"JSIMPLEX_TRACE_PIVOTS","0")=="1"
    previous_basis=Ref{Any}(nothing);small_pivots=Ref(0)
    observer=function(reason,ws)
        warming[] && return
        if reason==:pivot_completed && ws.iterations%5000==0
            println("PROGRESS iter=",ws.iterations," pinf=",JSimplex.primal_infeasibility(ws),
                " dinf=",JSimplex.dual_infeasibility(ws)," refs=",ws.refactorizations)
            flush(stdout)
        end
        if trace_pivots && reason==:pivot_proposed
            previous_basis[]=deepcopy(ws.basis)
            return
        elseif trace_pivots && reason==:pivot_completed && !isnothing(previous_basis[])
            row=ws.scratch.selected_row;entering=ws.scratch.selected_entering
            if row>0
                pivot=ws.scratch.row_solution[row]
                scale=norm(ws.scratch.row_solution,Inf)
                if abs(pivot)<parse(Float64,get(ENV,"JSIMPLEX_TRACE_RELATIVE","1e-8"))*scale && small_pivots[]<parse(Int,get(ENV,"JSIMPLEX_TRACE_LIMIT","10"))
                    small_pivots[]+=1
                    name=output*".accepted_pivot."*string(ws.iterations)*".bin"
                    serialize(name,(problem=ws.problem,basis=deepcopy(ws.basis),prior_basis=previous_basis[],
                        options=ws.options,costs=copy(ws.costs),lower=copy(ws.lower),upper=copy(ws.upper),
                        primal=copy(ws.primal),prices=copy(ws.reduced_costs),perturbed=ws.perturbed,
                        row=row,entering=entering,direction=copy(ws.scratch.row_solution),
                        rho=copy(ws.scratch.rho),tableau=copy(ws.scratch.tableau_row),iteration=ws.iterations))
                    println("SMALL_ACCEPTED_PIVOT iter=",ws.iterations," pivot=",pivot,
                        " direction_norm=",scale," relative_pivot=",abs(pivot)/scale," snapshot=",name);flush(stdout)
                end
            end
            return
        end
        reason in (:refactor_residual,:refactor_pivot,:correction_attempt,:phase_primal,
                   :phase_dual,:phase_one,:phase_auxiliary,:phase_cleanup,:certification_failed) || return
        count=get(events,reason,0)+1;events[reason]=count
        if count<=10 || count%100==0
            row=ws.scratch.selected_row;entering=ws.scratch.selected_entering
            println("EVENT ",reason," count=",count," iter=",ws.iterations,
                " row=",row," entering=",entering,
                " pinf=",JSimplex.primal_infeasibility(ws),
                " dinf=",JSimplex.dual_infeasibility(ws));flush(stdout)
            if reason in (:refactor_residual,:refactor_pivot) && 1<=row<=length(ws.scratch.row_solution) && entering>0
                println("PIVOT stored_forward=",ws.scratch.row_solution[row],
                    " stored_tableau=",ws.scratch.tableau_row[entering],
                    " direction_norm=",norm(ws.scratch.row_solution,Inf),
                    " row_residual_ratio=",JSimplex._dual_row_residual_ratio(ws,ws.scratch.rho,row));flush(stdout)
            end
        end
        marginal=algorithm=="dual" && reason==:correction_attempt && marginal_snapshots[]<3 &&
            ws.options.dual_tolerance<JSimplex.dual_infeasibility(ws)<=64ws.options.dual_tolerance
        failure=algorithm=="primal" && reason==:certification_failed
        if (reason==:refactor_residual && count in (1,10)) || marginal || failure
            name=output*"."*string(reason)*"."*string(ws.iterations)*".bin"
            if !isfile(name)
                marginal && (marginal_snapshots[]+=1)
                serialize(name,(problem=ws.problem,basis=deepcopy(ws.basis),
                    options=ws.options,costs=copy(ws.costs),lower=copy(ws.lower),upper=copy(ws.upper),
                    primal=copy(ws.primal),prices=copy(ws.reduced_costs),perturbed=ws.perturbed,
                    row=ws.scratch.selected_row,entering=ws.scratch.selected_entering,
                    direction=copy(ws.scratch.row_solution),rho=copy(ws.scratch.rho),
                    tableau=copy(ws.scratch.tableau_row),iteration=ws.iterations,
                    candidate=algorithm=="primal" ? copy(JSimplex._pivot_quality_buffers(ws).trial) : Float64[],
                    last_step=ws.scratch.last_primal_step))
                println("SNAPSHOT ",name);flush(stdout)
            end
        end
    end
    fixture=joinpath(dirname(dirname(pathof(JSimplex))),"test/fixtures/solver/afiro.mps")
    with_logger(NullLogger()) do
        JSimplex._solve_diagnosed(read_mps(fixture),JSimplex.SimplexDiagnostics(;observer,kernel_timing=true);
            options,relax_integrality=true)
    end
    warming[]=false
    problem=read_mps(path)
    d=JSimplex.SimplexDiagnostics(;observer,kernel_timing=true)
    timed=@timed JSimplex._solve_diagnosed(problem,d;options,relax_integrality=true)
    result=timed.value
    report=Dict("input"=>realpath(path),"input_sha256"=>bytes2hex(open(sha256,path)),
        "algorithm"=>algorithm,"basis_update"=>update,"interval"=>options.refactorization_interval,"julia"=>string(VERSION),
        "status"=>string(result.status),"message"=>result.message,
        "iterations"=>result.statistics.iterations,"refactorizations"=>result.statistics.refactorizations,
        "seconds"=>result.statistics.elapsed_seconds,"outer_seconds"=>timed.time,
        "allocated_bytes"=>timed.bytes,"peak_rss"=>Sys.maxrss(),
        "counts"=>Dict(string(k)=>v for (k,v) in d.counts if v!=0),
        "kernel_seconds"=>Dict(string(k)=>v/1e9 for (k,v) in d.kernel_nanoseconds if v!=0))
    if result.status==OPTIMAL
        report["objective"]=result.objective_value
        report["original_primal_certified"]=JSimplex._original_primal_feasible(problem,result.primal,options.primal_tolerance)
    end
    open(output,"w") do io;TOML.print(io,report);end
    println(report)
end
main()
