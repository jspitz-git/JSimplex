using JSimplex, Logging, Serialization, SHA, TOML, Profile, LinearAlgebra
function write_report(output, report, objective)
    isnothing(objective) || (report["objective"] = objective)
    serialize(output * ".report.bin", report)
    open(output, "w") do io
        TOML.print(io, report)
    end
end

function main()
    input,method,output=ARGS[1:3]
    lowercase(basename(realpath(input))) in ("big.mps","largo.mps","anymod.mps") && error("Excluded model")
    limit=parse(Int,get(ARGS,4,"26000"));seconds=parse(Float64,get(ARGS,5,"360"))
    problem=read_mps(input);digest=bytes2hex(open(sha256,input))
    seeds=[16000,19200,20800,24000];captured=Set{Int}();pending=Dict{Int,Any}()
    rows=Dict{String,Any}[];warm=Ref(true);last_interval=Ref(0);previous=Ref(time_ns())
    observer=function(reason,ws)
        warm[] && return
        if reason==:pivot_completed
            for (seed,data) in collect(pending)
                push!(data.steps,(ws.scratch.selected_row,ws.scratch.selected_entering))
                if length(data.steps)==320
                    serialize(output*".history."*string(seed)*".bin",data)
                    delete!(pending,seed)
                    println("CAPTURE seed=",seed," start=",data.iteration," steps=320");flush(stdout)
                end
            end
            if ws.iterations%80==0 || ws.dual_refactorization_interval!=last_interval[]
                f=ws.factorization;d=ws.progress.diagnostics
                triangular=f isa JSimplex.AbstractTriangularBasisFactorization
                record=Dict{String,Any}("iteration"=>ws.iterations,
                    "seconds"=>(time_ns()-ws.progress.start_ns)/1e9,
                    "configured_interval"=>ws.options.refactorization_interval,
                    "effective_interval"=>ws.dual_refactorization_interval,
                    "updates"=>length(f.updates),"refactorizations"=>ws.refactorizations,
                    "upper_entries"=>triangular ? sum(c->length(c.values),f.upper;init=0) : 0,
                    "history_entries"=>triangular ? sum(JSimplex._update_storage_count,f.updates;init=0) : sum(u->length(u.values),f.updates;init=0),
                    "working_objective"=>dot(ws.costs,ws.primal),
                    "kernels"=>Dict(string(k)=>v/1e9 for (k,v) in d.kernel_nanoseconds if v!=0))
                push!(rows,record)
                if ws.dual_refactorization_interval!=last_interval[] || ws.iterations%2000==0
                    println(record);flush(stdout)
                end
                last_interval[]=ws.dual_refactorization_interval
            end
        elseif reason==:refactor_limit
            for seed in seeds
                seed in captured && continue
                ws.iterations>=seed || continue
                push!(captured,seed)
                pending[seed]=(input=realpath(input),input_sha256=digest,A=ws.problem.A,
                    basis=copy(ws.basis.basic_indices),iteration=ws.iterations,steps=Tuple{Int,Int}[])
            end
        end
    end
    opts=SolverOptions(algorithm=:dual,basis_update=Symbol(method),basis_refactorization=:native,
        pricing=:steepest_edge,simplex_strategy=:legacy,refactorization_interval=80,
        time_limit=seconds,iteration_limit=limit,verbose=false)
    d=JSimplex.SimplexDiagnostics(;kernel_timing=true,observer)
    with_logger(NullLogger()) do
        JSimplex._solve_diagnosed(read_mps(joinpath(dirname(dirname(pathof(JSimplex))),"test/fixtures/solver/afiro.mps")),d;options=opts)
    end
    warm[]=false
    d=JSimplex.SimplexDiagnostics(;kernel_timing=true,observer)
    Profile.init(n=5_000_000,delay=0.005)
    measured=@timed @profile with_logger(NullLogger()) do
        JSimplex._solve_diagnosed(problem,d;options=opts,relax_integrality=true)
    end
    r=measured.value
    report=Dict("source_revision"=>strip(read(`git rev-parse HEAD`,String)),"input_sha256"=>digest,
        "method"=>method,"status"=>string(r.status),"iterations"=>r.statistics.iterations,
        "source_dirty"=>!isempty(strip(read(`git diff --name-only`,String))),
        "original_primal_certified"=>r.status==OPTIMAL && JSimplex._original_primal_feasible(problem,r.primal,opts.primal_tolerance),
        "seconds"=>r.statistics.elapsed_seconds,"allocated_bytes"=>measured.bytes,
        "peak_rss"=>Sys.maxrss(),"julia"=>string(VERSION),"samples"=>rows,
        "counts"=>Dict(string(k)=>v for (k,v) in d.counts if v!=0))
    println("FINAL ",r.status," iterations=",r.statistics.iterations," seconds=",r.statistics.elapsed_seconds);flush(stdout)
    write_report(output, report, r.objective_value)
    open(output*".profile","w") do io;Profile.print(io;format=:flat,sortedby=:count,mincount=40);end
end
abspath(PROGRAM_FILE) == (@__FILE__) && main()
