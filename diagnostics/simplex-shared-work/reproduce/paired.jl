using JSimplex, LinearAlgebra, SHA, TOML, Logging
const JS=JSimplex
const ROOT=dirname(dirname(pathof(JS)))
function measure(input,algorithm,manager,limit,interval)
    p=read_mps(input)
    options=SolverOptions(;algorithm,basis_update=manager,basis_refactorization=:native,
        pricing=:steepest_edge,simplex_strategy=:legacy,partial_pricing=false,
        iteration_limit=limit,time_limit=Inf,refactorization_interval=interval,verbose=false)
    events=SHA.SHA2_256_CTX();states=SHA.SHA2_256_CTX();latest=Ref{Any}(nothing)
    function checkpoint(ws)
        for a in (ws.basis.basic_indices,ws.basis.states,ws.primal,ws.reduced_costs,ws.costs,ws.pricing_weights)
            SHA.update!(states,reinterpret(UInt8,a))
        end
    end
    observer=(event,ws)->begin
        if event in (:pivot_completed,:flip_completed)
            SHA.update!(events,reinterpret(UInt8,[ws.progress.iteration_offset,ws.iterations,ws.scratch.selected_row,ws.scratch.selected_entering]))
            SHA.update!(events,reinterpret(UInt8,[ws.scratch.last_primal_step,ws.scratch.last_dual_step]))
            ws.iterations%80==0 && checkpoint(ws)
        end
        latest[]=ws
        nothing
    end
    d=JS.SimplexDiagnostics(;observer)
    r=with_logger(NullLogger()) do
        JS._solve_diagnosed(p,d;options,relax_integrality=true)
    end
    isnothing(latest[]) || checkpoint(latest[])
    row=Dict("input"=>input,"input_sha256"=>bytes2hex(open(sha256,input)),"algorithm"=>string(algorithm),"manager"=>string(manager),
        "iterations"=>r.statistics.iterations,"refactorizations"=>r.statistics.refactorizations,"status"=>string(r.status),
        "events_hash"=>bytes2hex(SHA.digest!(events)),"states_hash"=>bytes2hex(SHA.digest!(states)),
        "counts"=>Dict(string(k)=>v for (k,v) in d.counts),"seconds_instrumented"=>r.statistics.elapsed_seconds)
    if r.status==OPTIMAL
        row["original_feasible"]=JS._original_primal_feasible(p,r.primal,options.primal_tolerance)
        row["primal_hash"]=bytes2hex(sha256(reinterpret(UInt8,r.primal)))
        row["objective"]=r.objective_value
        @assert row["original_feasible"]
    end
    @assert r.status==(limit==1_000_000 ? OPTIMAL : ITERATION_LIMIT)
    println(basename(input)," ",algorithm," ",manager," ",row["status"]," ",row["iterations"]);flush(stdout)
    return row
end
function main(case,out)
    @assert !ispath(out)
    @assert Threads.nthreads()==BLAS.get_num_threads()==1
    rows=Any[]
    if case=="fast"
        for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub,:huangfu_hall),algorithm in (:primal,:dual)
            push!(rows,measure("/home/jspitz/mps/fast0507.mps",algorithm,manager,1_000_000,80))
        end
    elseif case=="medium"
        for algorithm in (:primal,:dual)
            push!(rows,measure("/home/jspitz/mps/medium.mps",algorithm,:huangfu_hall,algorithm==:primal ? 2000 : 4000,320))
        end
    else
        @assert case=="runtime"
        push!(rows,measure("/home/jspitz/mps/runtime.mps",:dual,:huangfu_hall,1_000_000,320))
        @assert isapprox(rows[1]["objective"],51425691.76210454;rtol=1e-8,atol=1e-7)
    end
    source=Dict(relpath(joinpath(d,f),ROOT)=>bytes2hex(open(sha256,joinpath(d,f))) for (d,_,fs) in walkdir(joinpath(ROOT,"src")) for f in fs if endswith(f,".jl"))
    open(out,"w") do io;TOML.print(io,Dict("cases"=>rows,"source_root"=>ROOT,"source_hashes"=>source));end
end
main(ARGS...)
