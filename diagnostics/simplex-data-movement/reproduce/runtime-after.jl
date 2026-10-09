# Read-only solver instrumentation: preserve original methods under private names.
using JSimplex,Serialization,TOML,SHA,Logging,LinearAlgebra
const JS=JSimplex
@eval JS begin
    const _guard_probe_times=Dict{Symbol,Tuple{Int,UInt64}}()
    const _guard_probe_capture=Ref{Any}(nothing)
    const _guard_probe_saved=Set{Tuple{Int,Int}}()
    function _guard_probe_record(key,start)
        count,elapsed=get(_guard_probe_times,key,(0,UInt64(0)))
        _guard_probe_times[key]=(count+1,elapsed+(time_ns()-start))
    end
end
function save_original(name,file)
    s=read(joinpath(dirname(pathof(JS)),file),String)
    ex,_=Meta.parse(s,first(findfirst("function "*string(name)*"(",s)))
    signature=ex.args[1]
    while signature.head != :call;signature=signature.args[1];end
    signature.args[1]=Symbol(:_guard_original_,name)
    Core.eval(JS,ex)
end
for (name,file) in ((:_finite_workspace,"dual_simplex.jl"),(:_dual_row_residual_ratio,"dual_simplex.jl"),(:_dual_direction_residual_ok!,"dual_simplex.jl"),(:_legacy_primal_point_certified,"legacy_primal_point.jl"))
    save_original(name,file)
end
@eval JS begin
    function _finite_workspace(ws::SimplexWorkspace{T}) where T
        started=time_ns()
        try;_guard_original__finite_workspace(ws)
        finally;_guard_probe_record(:finite_workspace,started);end
    end
    function _dual_row_residual_ratio(ws::SimplexWorkspace{T},rho::Vector{T},row::Int) where {T<:AbstractFloat}
        started=time_ns()
        result=try;_guard_original__dual_row_residual_ratio(ws,rho,row)
        finally;_guard_probe_record(:dual_row_residual,started);end
        isnothing(_guard_probe_capture[]) || _guard_probe_capture[](ws,rho,row,result)
        result
    end
    function _dual_direction_residual_ok!(ws::SimplexWorkspace{T},direction::Vector{T},pivot::T) where {T<:AbstractFloat}
        started=time_ns()
        try;_guard_original__dual_direction_residual_ok!(ws,direction,pivot)
        finally;_guard_probe_record(:dual_direction_residual,started);end
    end
    function _legacy_primal_point_certified(ws)
        started=time_ns()
        try;_guard_original__legacy_primal_point_certified(ws)
        finally;_guard_probe_record(:primal_point_certificate,started);end
    end
end
function run(input,algorithm,limit,out)
    mkdir(out)
    options=SolverOptions(;algorithm,basis_update=:huangfu_hall,basis_refactorization=:native,
        refactorization_interval=320,pricing=:steepest_edge,simplex_strategy=:legacy,
        partial_pricing=false,verbose=false,time_limit=Inf,iteration_limit=limit)
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
        latest[]=ws;nothing
    end
    warm=read_mps(joinpath(dirname(dirname(pathof(JS))),"test/fixtures/solver/afiro.mps"))
    with_logger(NullLogger()) do
        JS._solve_diagnosed(warm,JS.SimplexDiagnostics(;observer,kernel_timing=true);options,relax_integrality=true)
    end
    empty!(JS._guard_probe_times);empty!(JS._guard_probe_saved)
    events=SHA.SHA2_256_CTX();states=SHA.SHA2_256_CTX();latest[]=nothing
    targets=Set([0,80,1000,1999,3999,10000,30000,50000])
    function capture(ws,rho,row,ratio)
        key=(ws.progress.iteration_offset,ws.iterations)
        ws.iterations in targets && key ∉ JS._guard_probe_saved || return
        length(JS._guard_probe_saved)<16 || return
        push!(JS._guard_probe_saved,key)
        serialize(joinpath(out,"row-$(key[1])-$(key[2]).bin"),
            (;A=ws.problem.A,basics=ws.basis.basic_indices,states=ws.basis.states,rho,row,ratio,
              tolerance=ws.options.zero_tolerance,iteration=ws.iterations,offset=ws.progress.iteration_offset))
        println("SNAPSHOT ",basename(input)," ",algorithm," ",key," ratio=",ratio);flush(stdout)
    end
    JS._guard_probe_capture[]=capture
    problem=read_mps(input);d=JS.SimplexDiagnostics(;observer,kernel_timing=true)
    t=@timed with_logger(NullLogger()) do
        JS._solve_diagnosed(problem,d;options,relax_integrality=true)
    end
    JS._guard_probe_capture[]=nothing
    r=t.value;isnothing(latest[]) || checkpoint(latest[])
    result=Dict("input"=>input,"algorithm"=>string(algorithm),"status"=>string(r.status),"message"=>r.message,
        "iterations"=>r.statistics.iterations,"refactorizations"=>r.statistics.refactorizations,
        "seconds"=>t.time,"compile_seconds"=>t.compile_time,"allocated_bytes"=>t.bytes,"peak_rss"=>Sys.maxrss(),
        "events_hash"=>bytes2hex(SHA.digest!(events)),"states_hash"=>bytes2hex(SHA.digest!(states)),
        "guard_calls"=>Dict(string(k)=>v[1] for (k,v) in JS._guard_probe_times),
        "guard_seconds_inclusive"=>Dict(string(k)=>v[2]/1e9 for (k,v) in JS._guard_probe_times),
        "counts"=>Dict(string(k)=>v for (k,v) in d.counts),
        "kernel_seconds"=>Dict(string(k)=>v/1e9 for (k,v) in d.kernel_nanoseconds),
        "input_sha256"=>bytes2hex(open(sha256,input)),"source_revision"=>strip(read(`git rev-parse HEAD`,String)))
    if r.status==OPTIMAL
        result["objective"]=r.objective_value
        result["original_feasible"]=JS._original_primal_feasible(problem,r.primal,options.primal_tolerance)
        @assert result["original_feasible"]
    end
    open(joinpath(out,"result.toml"),"w") do io;TOML.print(io,result);end
    println("RESULT ",basename(input)," ",algorithm," ",r.status," ",r.statistics.iterations);flush(stdout)
    @assert r.status==(limit==1_000_000 ? OPTIMAL : ITERATION_LIMIT)
end
function main(out)
    @assert Threads.nthreads()==BLAS.get_num_threads()==1
    for (name,algorithm,limit) in (("fast0507",:dual,1_000_000),("medium",:dual,4000),("medium",:primal,2000),("runtime",:dual,1_000_000))
        run("/home/jspitz/mps/"*name*".mps",algorithm,limit,joinpath(out,name*"-"*string(algorithm)))
    end
end
Base.invokelatest(run,"/home/jspitz/mps/runtime.mps",:dual,1_000_000,only(ARGS))
