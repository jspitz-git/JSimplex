using JSimplex, LinearAlgebra, Logging, Profile, TOML, SHA
const JS=JSimplex
function report_run(problem,options)
 t=@timed with_logger(NullLogger()) do
  solve(problem;options,relax_integrality=true)
 end
 r=t.value
 @assert r.status==OPTIMAL
 @assert JS._original_primal_feasible(problem,r.primal,options.primal_tolerance)
 Dict("status"=>string(r.status),"iterations"=>r.statistics.iterations,
  "refactorizations"=>r.statistics.refactorizations,"objective"=>r.objective_value,
  "seconds"=>t.time,"compile_seconds"=>t.compile_time,"gc_seconds"=>t.gctime,
  "allocations"=>Base.gc_alloc_count(t.gcstats),"bytes"=>t.bytes,"original_feasible"=>true)
end
function main(input,out)
 @assert Threads.nthreads()==BLAS.get_num_threads()==1
 options=SolverOptions(algorithm=:dual,basis_update=:huangfu_hall,basis_refactorization=:native,
  refactorization_interval=320,pricing=:steepest_edge,simplex_strategy=:legacy,
  partial_pricing=false,iteration_limit=1_000_000,time_limit=Inf,verbose=false)
 problem=read_mps(input)
 warm=read_mps(joinpath(dirname(dirname(pathof(JS))),"test/fixtures/solver/afiro.mps"))
 report_run(warm,options)
 GC.gc();plain=report_run(problem,options)
 open(out*"-plain.toml","w") do io;TOML.print(io,plain);end
 println("PLAIN ",plain);flush(stdout)
 rate=0.0001
 Profile.Allocs.clear();GC.gc();Profile.Allocs.start(;sample_rate=rate)
 sampled=try;report_run(problem,options);finally;Profile.Allocs.stop();end
 for k in ("status","iterations","refactorizations","objective");@assert plain[k]==sampled[k];end
 data=Profile.Allocs.fetch().allocs
 groups=Dict{Tuple{String,String,String},Tuple{Int,Int}}()
 examples=Dict{Tuple{String,String,String},Vector{String}}()
 sizes=Dict{String,Int}()
 for a in data
  frames=[string(f.func,"@",f.file,":",f.line) for f in a.stacktrace]
  project=filter(f->occursin("JSimplex.jl/src/",f),frames)
  compiler=any(f->occursin("/Compiler/",f)||occursin("compiler/",f)||occursin("typeinf",f),frames)
  site=isempty(project) ? "outside_solver" : first(project)
  category=compiler ? "compilation" : any(f->occursin("presolve",f),project) ? "presolve" :
   any(f->occursin("cleanup",f)||occursin("postsolve",f),project) ? "cleanup_or_postsolve" :
   any(f->occursin("correction",f)||occursin("refine",f)||occursin("certificate",f),project) ? "correction_or_certification" :
   any(f->occursin("recompute!",f)||occursin("factorize",f),project) ? "refactorization_or_recompute" :
   any(f->occursin("dual_iteration",f),project) ? "ordinary_dual_iteration" : "other"
  key=(category,site,string(a.type));n,b=get(groups,key,(0,0));groups[key]=(n+1,b+a.size)
  haskey(examples,key) || (examples[key]=frames)
  bucket=a.size<=128 ? "0_128" : a.size<=1024 ? "129_1024" : "over1024"
  sizes[bucket]=get(sizes,bucket,0)+1
 end
 rows=[Dict("category"=>k[1],"site"=>k[2],"type"=>k[3],"samples"=>v[1],
  "sampled_bytes"=>v[2],"estimated_allocations"=>v[1]/rate,
  "estimated_bytes"=>v[2]/rate,"example_stack"=>examples[k]) for (k,v) in groups]
 sort!(rows;by=r->-r["samples"])
 report=Dict("plain"=>plain,"sampled"=>sampled,"rate"=>rate,"sample_count"=>length(data),
  "size_buckets"=>sizes,"groups"=>rows,"input"=>input,"input_sha256"=>bytes2hex(open(sha256,input)))
 open(out*"-allocations.toml","w") do io;TOML.print(io,report);end
 println("SAMPLED ",length(data)," ",sampled);flush(stdout)
end
Base.invokelatest(main,ARGS...)
