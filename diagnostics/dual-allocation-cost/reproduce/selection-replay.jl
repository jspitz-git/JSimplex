using JSimplex,Serialization,LinearAlgebra,TOML,Statistics
const JS=JSimplex
function options_pricing(o,p)
 values=NamedTuple{fieldnames(typeof(o))}(Tuple(getfield(o,k) for k in fieldnames(typeof(o))))
 SolverOptions(Float64;values...,pricing=p,basis_update=o.basis_update,basis_refactorization=o.basis_refactorization)
end
function batch(w,index,original,alternate)
 for repeat in 1:20
  w.primal[index]=isodd(repeat) ? original : alternate
  Base.donotdelete(JS._dual_edge_selection(w,Val(Float64)))
 end
 nothing
end
function main(directory,out)
 @assert Threads.nthreads()==BLAS.get_num_threads()==1
 files=sort(filter(p->occursin("-state-",p)&&endswith(p,".bin"),readdir(directory;join=true)))
 rows=[]
 for path in files
  d=deserialize(path);w=JS._initialize_workspace_state(d.problem,d.options)
  for (target,source) in ((w.basis.basic_indices,d.basics),(w.basis.states,d.states),(w.primal,d.primal),(w.pricing_weights,d.weights),(w.lower,d.lower),(w.upper,d.upper),(w.reduced_costs,d.reduced),(w.costs,d.costs))
   copyto!(target,source)
  end
  methods=(:dantzig,:devex,:steepest_edge);opts=map(p->options_pricing(d.options,p),methods)
  selected=Int[]
  samples=[Float64[] for _ in 1:3];allocs=[Int[] for _ in 1:3];batch_bytes=[Int[] for _ in 1:3];batch_allocs=[Int[] for _ in 1:3];compiles=[Float64[] for _ in 1:3]
  index=d.basics[1];original=w.primal[index];alternate=isfinite(original) ? nextfloat(original) : original
  for o in opts;w.options=o;push!(selected,JS._dual_edge_selection(w,Val(Float64)));batch(w,index,original,alternate);end
  for round in 1:9
   for k in circshift(collect(1:3),round%3)
    w.options=opts[k];GC.gc()
    t=@timed batch(w,index,original,alternate)
    @assert t.compile_time==0
    push!(samples[k],t.time/20);push!(allocs[k],t.bytes÷20);push!(batch_bytes[k],t.bytes);push!(batch_allocs[k],Base.gc_alloc_count(t.gcstats));push!(compiles[k],t.compile_time)
   end
  end
  for k in 1:3
   push!(rows,Dict("snapshot"=>basename(path),"iteration"=>d.iteration,"offset"=>d.offset,"phase"=>d.phase,"selected_row"=>selected[k],"rows"=>length(d.basics),"variables"=>length(d.states),"pricing"=>string(methods[k]),"seconds"=>samples[k],"bytes"=>allocs[k],"batch_bytes"=>batch_bytes[k],"batch_allocations"=>batch_allocs[k],"compile_seconds"=>compiles[k],"median_seconds"=>median(samples[k])))
  end
  open(out,"w") do io;TOML.print(io,Dict("cases"=>rows));end
  println("REPLAY ",basename(path));flush(stdout)
 end
 @assert !isempty(rows)
end
Base.invokelatest(main,ARGS...)
