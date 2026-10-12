using JSimplex,Test,SparseArrays,LinearAlgebra,TOML,SHA
const JS=JSimplex
const ROOT=dirname(dirname(pathof(JS)))
const HELPERS=first(split(read(joinpath(ROOT,"test/restoration_alias_copy_tests.jl"),String),"@testset \"Restoration copy ownership"))
include_string(Main,HELPERS,"restoration test helpers")
function fixture(T,n,detached,bounds)
 p=LinearProblem(spzeros(T,0,n),ones(T,n))
 w=JS.initialize_workspace(p,SolverOptions(T;verbose=false))
 j=JS.PerturbationJournal(w);w.scratch.perturbations=j
 w.costs=detached ? copy(j.active_costs) : j.active_costs
 if bounds
  j.bounds=JS.BoundPerturbationState(w)
  w.lower=j.bounds.active_lower;w.upper=j.bounds.active_upper
 end
 w,j
end
function batch!(f,w,j,bounds,repeats)
 for _ in 1:repeats
  j.active=true
  bounds && (j.bounds.active=true)
  f(w,j)
 end
 nothing
end
function measured(f,w,j,bounds,repeats)
 @timed batch!(f,w,j,bounds,repeats)
end
function main(out)
 @assert !ispath(out)
 @assert Threads.nthreads()==BLAS.get_num_threads()==1
 samples=Any[];fixtures=0
 for T in (Float16,Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt})
  sizes=T===Float64 ? (32,8192,262144) : (32,8192)
  for n in sizes,detached in (false,true),bounds in (false,true)
   fixtures+=1; a,ja=fixture(T,n,detached,bounds);b,jb=fixture(T,n,detached,bounds)
   repeats=max(4,min(128,262144÷n))
   measured(restoration_legacy_copy!,a,ja,bounds,repeats)
   measured(JS.restore_perturbations!,b,jb,bounds,repeats)
   GC.gc(true)
   for round in 1:3
    order=isodd(round) ? (:baseline,:candidate) : (:candidate,:baseline)
    for side in order
     w,j,f=side==:baseline ? (a,ja,restoration_legacy_copy!) : (b,jb,JS.restore_perturbations!)
     t=measured(f,w,j,bounds,repeats)
     @assert t.compile_time==0
     @assert !j.active && all(isone,w.costs) && all(isone,j.original_costs)
     @assert !bounds || !j.bounds.active
     push!(samples,Dict("type"=>string(T),"n"=>n,"detached"=>detached,"bounds"=>bounds,
      "round"=>round,"side"=>string(side),"repeats"=>repeats,"elapsed"=>t.time,
      "compile"=>t.compile_time,"gc"=>t.gctime,"bytes"=>t.bytes,
      "allocations"=>Base.gc_alloc_count(t.gcstats),
      "cost_copies_per_restore"=>side==:candidate && !detached ? 1 : 2,
      "bound_copies_per_restore"=>bounds ? 4 : 0))
    end
    @assert isequal(a.costs,b.costs) && isequal(ja.active_costs,jb.active_costs)
    @assert a.lower==b.lower && a.upper==b.upper
    @assert a.scratch.phase_generation==b.scratch.phase_generation
   end
  end
 end
 open(out,"w") do io
  TOML.print(io,Dict("samples"=>samples,"fixture_count"=>fixtures,
   "source_sha256"=>bytes2hex(sha256(read(joinpath(ROOT,"src/simplex_perturbation.jl")))),
   "script_sha256"=>bytes2hex(sha256(read(@__FILE__))),
   "scope"=>"Warm repeated cold-restoration kernel plus identical journal rearming; initialization excluded; no natural-frequency or solver speedup claim"))
 end
 println("RESTORATION_COST_PASS fixtures=",fixtures," samples=",length(samples))
end
Base.invokelatest(main,only(ARGS))
