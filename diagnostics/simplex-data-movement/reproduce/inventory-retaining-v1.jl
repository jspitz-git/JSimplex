using JSimplex,Serialization,TOML,SHA,Logging,LinearAlgebra,Profile
const JS=JSimplex
@eval JS begin
 const _movement_counts=Dict{Symbol,Tuple{Int,UInt64}}()
 const _movement_basis=IdDict{Any,Any}()
 const _movement_repeated=Ref(0)
 function _movement_record(k,t)
  n,s=get(_movement_counts,k,(0,UInt64(0)));_movement_counts[k]=(n+1,s+time_ns()-t)
 end
end
function original(name,file)
 s=read(joinpath(dirname(pathof(JS)),file),String);ex,_=Meta.parse(s,first(findfirst("function "*string(name)*"(",s)))
 sig=ex.args[1];while sig.head!=:call;sig=sig.args[1];end
 sig.args[1]=Symbol(:_movement_original_,name);Core.eval(JS,ex)
end
for (n,f) in ((:_basis_matrix!,"simplex.jl"),(:_try_native_dual_correction!,"legacy_dual_correction.jl"),(:_try_native_dual_tableau!,"legacy_dual_correction.jl"),(:_audit_primal_values!,"primal_updates.jl"))
 original(n,f)
end
@eval JS begin
 function _basis_matrix!(ws::SimplexWorkspace)
  t=time_ns();b=try;_movement_original__basis_matrix!(ws);finally;_movement_record(:basis_assembly,t);end
  key=(ws.progress.iteration_offset,ws.iterations)
  old=get(_movement_basis,ws,nothing)
  if !isnothing(old) && old[1]==key && old[2]==ws.basis.basic_indices
   _movement_repeated[]+=1
  else
   _movement_basis[ws]=(key,copy(ws.basis.basic_indices))
  end
  b
 end
 function _try_native_dual_correction!(ws::SimplexWorkspace{T},d::Vector{T},i::Int,row::Int,stop;transposed::Bool=false) where T
  t=time_ns()
  try;_movement_original__try_native_dual_correction!(ws,d,i,row,stop;transposed)
  finally;_movement_record(transposed ? :row_correction : :direction_correction,t);end
 end
 function _try_native_dual_tableau!(ws::SimplexWorkspace{T},row,entering,orientation,violation,flips,stop;reselect=false) where {T<:Union{Float32,Float64}}
  t=time_ns()
  try;_movement_original__try_native_dual_tableau!(ws,row,entering,orientation,violation,flips,stop;reselect)
  finally;_movement_record(:tableau_recovery,t);end
 end
 function _audit_primal_values!(ws::SimplexWorkspace{T})::Symbol where T
  t=time_ns();try;_movement_original__audit_primal_values!(ws)
  finally;_movement_record(:primal_audit,t);end
 end
end
function main(case,out)
 @assert !ispath(out)
 @assert Threads.nthreads()==BLAS.get_num_threads()==1
 cleanup=startswith(case,"cleanup-")
 if cleanup
  input="/home/jspitz/.codex/worktrees/simplex-certificate-repair/JSimplex.jl/.superpowers/certificate-repair/medium-"*split(case,'-')[2]*"-handoff.bin"
  d=deserialize(input);p=d.problem;limit=d.iterations+512
  options=JS._remaining_options(d.options;iterations=d.options.iteration_limit-limit,time_limit=Inf)
 else
  algorithm=endswith(case,"primal") ? :primal : :dual
  input="/home/jspitz/mps/"*(startswith(case,"runtime") ? "runtime" : "medium")*".mps"
  p=read_mps(input);options=SolverOptions(;algorithm,basis_update=:huangfu_hall,basis_refactorization=:native,refactorization_interval=320,pricing=:steepest_edge,simplex_strategy=:legacy,partial_pricing=false,time_limit=Inf,iteration_limit=startswith(case,"runtime") ? 1_000_000 : algorithm==:primal ? 2000 : 4000,verbose=false)
 end
 phases=Dict{String,Int}();windows=[];last=Ref((time_ns(),Base.gc_bytes()));latest=Ref{Any}(nothing)
 observer=(event,ws)->begin
  latest[]=ws
  startswith(string(event),"phase_") && (phases[string(event)]=get(phases,string(event),0)+1)
  if event in (:pivot_completed,:flip_completed) && ws.iterations%256==0
   now=time_ns();bytes=Base.gc_bytes();push!(windows,Dict("iteration"=>ws.iterations,"offset"=>ws.progress.iteration_offset,"seconds"=>(now-last[][1])/1e9,"allocated_bytes"=>bytes-last[][2]));last[]=(now,bytes)
  end
  nothing
 end
 warm=read_mps(joinpath(dirname(dirname(pathof(JS))),"test/fixtures/solver/afiro.mps"))
 with_logger(NullLogger()) do;solve(warm;options,relax_integrality=true);end
 empty!(JS._movement_counts);empty!(JS._movement_basis);JS._movement_repeated[]=0
 diag=JS.SimplexDiagnostics(;observer,kernel_timing=true)
 Profile.clear();Profile.init(n=8_000_000,delay=0.01);GC.gc();last[]=(time_ns(),Base.gc_bytes())
 measured=@timed @profile with_logger(NullLogger()) do
  if cleanup
   ctx=JS.SolveContext(time_ns(),Inf,diag,JS.NumericalPolicy(Float64,options))
   JS.cleanup_original(p,d.basis,options,ctx,d.iterations,d.refactorizations;target_primal=d.target_primal)
  else
   JS._solve_diagnosed(p,diag;options,relax_integrality=true)
  end
 end
 r=measured.value
 report=Dict("case"=>case,"input_sha256"=>bytes2hex(open(sha256,input)),"status"=>string(r.status),"iterations"=>cleanup ? r.iterations : r.statistics.iterations,"seconds"=>measured.time,"compile_seconds"=>measured.compile_time,"gc_seconds"=>measured.gctime,"allocated_bytes"=>measured.bytes,"basis_same_iteration_repeats"=>JS._movement_repeated[],"calls"=>Dict(string(k)=>v[1] for (k,v) in JS._movement_counts),"inclusive_seconds"=>Dict(string(k)=>v[2]/1e9 for (k,v) in JS._movement_counts),"phases"=>phases,"windows"=>windows,"events"=>Dict(string(k)=>v for (k,v) in diag.counts if v!=0),"kernel_seconds"=>Dict(string(k)=>v/1e9 for (k,v) in diag.kernel_nanoseconds if v!=0),"revision"=>strip(read(`git rev-parse HEAD`,String)))
 if r.status==OPTIMAL
  report["original_feasible"]=JS._original_primal_feasible(p,r.primal,options.primal_tolerance);@assert report["original_feasible"]
 end
 open(out,"w") do io;TOML.print(io,report);end
 open(out*".profile","w") do io;Profile.print(io;format=:flat,sortedby=:count,mincount=5,C=false);end
 println(case," ",r.status," ",report["iterations"]);flush(stdout)
 @assert r.status==(case=="runtime-dual" ? OPTIMAL : ITERATION_LIMIT)
end
Base.invokelatest(main,ARGS...)
