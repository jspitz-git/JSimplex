# Diagnostic-only cold-boundary instrumentation. Solver arithmetic is unchanged.
using JSimplex, LinearAlgebra, SparseArrays, Serialization, TOML, SHA
const JS=JSimplex
const ENABLED=Ref(false)
const OUT=ARGS[1]
const RECORDS=Dict{String,Any}[]
struct CaptureComplete <: Exception end
function snapshot(ws,tag)
    f=ws.factorization;lu=f.base.factorization
    base=SparseMatrixCSC(lu.m,lu.n,lu.colptr .+ 1,lu.rowval .+ 1,copy(lu.nzval))
    fields=Dict(k=>getfield(ws,k) for k in fieldnames(typeof(ws)) if k ∉ (:progress,:factorization))
    progress=Dict(k=>getfield(ws.progress,k) for k in fieldnames(typeof(ws.progress)) if k != :diagnostics)
    factor=Dict(k=>getfield(f,k) for k in fieldnames(typeof(f)) if k != :base)
    serialize(joinpath(OUT,tag*".bin"),(;fields,progress,factor,base,base_control=lu.control))
end
function terminal(ws,status,message,tag;stop=false)
    ENABLED[] || return
    d=ws.progress.diagnostics
    r=Dict{String,Any}("tag"=>tag,"status"=>string(status),"message"=>message,
      "iterations"=>ws.iterations,"offset"=>ws.progress.iteration_offset,
      "refactorizations"=>ws.refactorizations,"rows"=>size(ws.problem.A,1),
      "columns"=>size(ws.problem.A,2),"pinf"=>JS.primal_infeasibility(ws),
      "dinf"=>JS.dual_infeasibility(ws),"algorithm"=>string(ws.options.algorithm),
      "updates"=>length(ws.factorization.updates),"events"=>Dict(string(k)=>v for (k,v) in d.counts))
    push!(RECORDS,r);println("BOUNDARY ",r);flush(stdout)
    open(joinpath(OUT,"boundaries.toml"),"w") do io;TOML.print(io,Dict("boundaries"=>RECORDS));end
    if status==NUMERICAL_ERROR || tag=="internal"
        snapshot(ws,string(length(RECORDS),"-",tag))
    end
    stop && status==NUMERICAL_ERROR && throw(CaptureComplete())
end
function clone(file,name,newname)
    source=read(joinpath(dirname(pathof(JS)),file),String)
    ex,_=Meta.parse(source,first(findfirst("function "*string(name)*"(",source)))
    sig=ex.args[1];while sig.head!=:call;sig=sig.args[1];end
    sig.args[1]=newname;Core.eval(JS,ex)
end
clone("dual_simplex.jl",:_internal_solution,:_bg_saved_internal)
clone("dual_simplex.jl",:_dual_optimize!,:_bg_saved_dual!)
clone("primal_simplex.jl",:_primal_optimize!,:_bg_saved_primal!)
@eval JS begin
 function _internal_solution(ws::SimplexWorkspace{T},status::TerminationStatus,message::String) where T
    Main.terminal(ws,status,message,"internal";stop=true)
    _bg_saved_internal(ws,status,message)
 end
 function _dual_optimize!(ws::SimplexWorkspace{T},stop;perturb_degenerate::Bool=true)::DualTermination where T
    result=_bg_saved_dual!(ws,stop;perturb_degenerate)
    Main.terminal(ws,result.status,result.message,"dual")
    result
 end
 function _primal_optimize!(ws::SimplexWorkspace{T},stop,tolerance::T=ws.options.dual_tolerance;perturb_degenerate::Bool=true) where T
    result=_bg_saved_primal!(ws,stop,tolerance;perturb_degenerate)
    Main.terminal(ws,result.status,result.message,"primal")
    result
 end
end
function main()
    @assert Threads.nthreads()==BLAS.get_num_threads()==1
    options=SolverOptions(algorithm=:dual,basis_update=:bartels_golub,
      basis_refactorization=:native,refactorization_interval=320,pricing=:steepest_edge,
      simplex_strategy=:legacy,partial_pricing=false,time_limit=Inf,iteration_limit=1_000_000,verbose=true)
    warm=read_mps(joinpath(dirname(dirname(pathof(JS))),"test/fixtures/solver/afiro.mps"))
    JS._solve_diagnosed(warm,JS.SimplexDiagnostics();options,relax_integrality=true)
    ENABLED[]=true
    input="/home/jspitz/mps/runtime.mps"
    @assert bytes2hex(open(sha256,input))=="d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68"
    try
        r=JS._solve_diagnosed(read_mps(input),JS.SimplexDiagnostics();options,relax_integrality=true)
        error("Expected numerical boundary was not reached: $(r.status)")
    catch e
        e isa CaptureComplete || rethrow()
        println("CAPTURE_COMPLETE: stopped deliberately at first numerical terminal")
    end
end
Base.invokelatest(main)
