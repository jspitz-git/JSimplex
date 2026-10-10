using JSimplex,LinearAlgebra,SparseArrays,Logging,TOML,SHA,Serialization,Profile
const JS=JSimplex
include("counters.jl")
function run_case(case,out,mode;steps=nothing)
 cleanup=startswith(case,"cleanup")
 algorithm=endswith(case,"primal") ? :primal : :dual
 input=cleanup ? "/home/jspitz/.codex/worktrees/simplex-certificate-repair/JSimplex.jl/.superpowers/certificate-repair/medium-$(algorithm)-handoff.bin" : "/home/jspitz/mps/medium.mps"
 readtime=@elapsed data=cleanup ? deserialize(input) : read_mps(input)
 p=cleanup ? data.problem : data
 count=isnothing(steps) ? (cleanup ? 256 : algorithm==:primal ? 2000 : 4000) : steps
 options=cleanup ? JS._remaining_options(data.options;iterations=data.options.iteration_limit-(data.iterations+count),time_limit=Inf) : SolverOptions(;algorithm,basis_update=:huangfu_hall,basis_refactorization=:native,refactorization_interval=320,pricing=:steepest_edge,simplex_strategy=:legacy,partial_pricing=false,time_limit=Inf,iteration_limit=count,verbose=false)
 events=SHA.SHA2_256_CTX();states=SHA.SHA2_256_CTX();ints=zeros(Int,4);floats=zeros(2)
 latest=Ref{Any}(nothing);windows=Any[];phases=Any[];last=Ref((time_ns(),Base.gc_num()));previous=Ref(0)
 instrumented=mode=="census"
 function checkpoint(w)
  for a in (w.basis.basic_indices,w.basis.states,w.primal,w.reduced_costs,w.costs,w.pricing_weights)
   SHA.update!(states,reinterpret(UInt8,a))
  end
 end
 function observe(event,w)
  latest[]=w
  if startswith(string(event),"phase_")
   push!(phases,Dict("event"=>string(event),"iteration"=>w.iterations,"offset"=>w.progress.iteration_offset,"rows"=>size(w.problem.A,1),"columns"=>size(w.problem.A,2),"nnz"=>nnz(w.problem.A)))
  end
  if event in (:pivot_completed,:flip_completed)
   ints.=(w.progress.iteration_offset,w.iterations,w.scratch.selected_row,w.scratch.selected_entering)
   floats.=(w.scratch.last_primal_step,w.scratch.last_dual_step)
   SHA.update!(events,reinterpret(UInt8,ints));SHA.update!(events,reinterpret(UInt8,floats))
   if w.iterations%128==0
    checkpoint(w);now=time_ns();g=Base.gc_num();delta=Base.GC_Diff(g,last[][2])
    push!(windows,Dict("iteration"=>w.iterations,"offset"=>w.progress.iteration_offset,"seconds"=>(now-last[][1])/1e9,"bytes"=>delta.allocd,"allocations"=>Base.gc_alloc_count(delta),"gc_seconds"=>delta.total_time/1e9))
    last[]=(now,g)
   end
  end
  nothing
 end
 observer=(event,w)->begin
  if instrumented
   token=JS._tb_begin();try;observe(event,w);finally;JS._tb_end(2,token);end
  else;observe(event,w);end
 end
 diag=JS.SimplexDiagnostics(;observer,kernel_timing=false)
 function solve_case()
  with_logger(NullLogger()) do
   if cleanup
    ctx=JS.SolveContext(time_ns(),Inf,diag,JS.NumericalPolicy(Float64,options))
    JS.cleanup_original(p,deepcopy(data.basis),options,ctx,data.iterations,data.refactorizations;target_primal=data.target_primal)
   else
    JS._solve_diagnosed(p,diag;options,relax_integrality=true)
   end
  end
 end
 Profile.clear();Profile.init(n=8_000_000,delay=0.005)
 GC.gc(true);JS._tb_reset();last[]=(time_ns(),Base.gc_num())
 measured=@timed if mode=="profile"
  @profile solve_case()
 elseif instrumented
  t=JS._tb_begin();try;solve_case();finally;JS._tb_end(1,t);end
 else;solve_case();end
 result=measured.value
 isnothing(latest[]) || checkpoint(latest[])
 r=Dict("case"=>case,"mode"=>mode,"status"=>string(result.status),"iterations"=>(cleanup ? result.iterations : result.statistics.iterations),"seconds"=>measured.time,"compile_seconds"=>measured.compile_time,"gc_seconds"=>measured.gctime,"bytes"=>measured.bytes,"allocations"=>Base.gc_alloc_count(measured.gcstats),"read_seconds"=>readtime,"input"=>input,"input_sha256"=>bytes2hex(open(sha256,input)),"events_hash"=>bytes2hex(SHA.digest!(events)),"states_hash"=>bytes2hex(SHA.digest!(states)),"events"=>Dict(string(k)=>v for (k,v) in diag.counts if v!=0),"phases"=>phases,"windows"=>windows,"original_rows"=>size(p.A,1),"original_columns"=>size(p.A,2),"original_nnz"=>nnz(p.A),"julia"=>string(VERSION),"threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),"source_revision"=>strip(read(`git rev-parse HEAD`,String)))
 if instrumented
  r["counters"]=counter_rows()
  @assert JS._tb_depth[]==0
  @assert sum(JS._tb_stats[:,6])==JS._tb_stats[1,2]
  @assert sum(JS._tb_stats[:,7])==JS._tb_stats[1,3]
  @assert sum(JS._tb_stats[:,8])==JS._tb_stats[1,4]
 end
 if mode=="profile"
  open(out*".flat.txt","w") do io;Profile.print(io;format=:flat,sortedby=:count,mincount=3,C=true);end
  open(out*".tree.txt","w") do io;Profile.print(io;format=:tree,mincount=10,maxdepth=40,C=false);end
 end
 if result.status==OPTIMAL
  r["original_feasible"]=JS._original_primal_feasible(p,result.primal,options.primal_tolerance);@assert r["original_feasible"]
 end
 open(out,"w") do io;TOML.print(io,r);end
 @assert result.status==ITERATION_LIMIT
 println(case," ",mode," ",r["seconds"]," compile=",r["compile_seconds"]," iterations=",r["iterations"]);flush(stdout)
 latest[]=nothing;GC.gc(true)
 r
end
function main(case,dir)
 @assert Threads.nthreads()==BLAS.get_num_threads()==1
 calibration_report=calibration()
 open(joinpath(dir,"calibration.toml"),"w") do io;TOML.print(io,Dict("probes"=>calibration_report));end
 run_case(case,joinpath(dir,"warm.toml"),"warm";steps=32)
 reference=run_case(case,joinpath(dir,"plain.toml"),"plain")
 sampled=run_case(case,joinpath(dir,"profile.toml"),"profile")
 for k in ("iterations","status","events_hash","states_hash","events");@assert reference[k]==sampled[k] k;end
 install_hooks()
 Base.invokelatest(run_case,case,joinpath(dir,"census-warm.toml"),"census";steps=32)
 census=Base.invokelatest(run_case,case,joinpath(dir,"census.toml"),"census")
 for k in ("iterations","status","events_hash","states_hash","events");@assert reference[k]==census[k] k;end
 println("IDENTICAL ",case);flush(stdout)
end
main(ARGS...)
