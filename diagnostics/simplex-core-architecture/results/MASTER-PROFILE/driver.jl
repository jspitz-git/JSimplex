# Current-master characterization. No methods or solver source are replaced.
const LOAD_START=time_ns()
using JSimplex, SparseArrays, TOML, Profile
const ROOT=normpath(joinpath(@__DIR__,"../../../.."))
realpath(pathof(JSimplex))==realpath(joinpath(ROOT,"src/JSimplex.jl")) || error("wrong source")
const Q=Rational{BigInt}
token(x::Float64)=bitstring(x)
token(x::BigFloat)=(string(Q(x)),precision(x),iszero(x)&&signbit(x))
token(x::Q)=string(x)
token(x::Union{Integer,Enum,Symbol,AbstractString,Nothing})=string(x)
token(x::AbstractArray)=map(token,x)
token(x::SparseMatrixCSC)=(size(x),token(x.colptr),token(x.rowval),token(x.nzval))
token(x)=map(f->token(getfield(x,f)),fieldnames(typeof(x)))
signature(s)=(s.status,token(s.objective_value),token(s.primal),s.statistics.iterations,s.statistics.refactorizations,s.message)
@noinline plain(p,o)=JSimplex.solve(p;options=o)
@noinline diagnosed(p,o,d)=JSimplex._solve_diagnosed(p,d;options=o)
function metrics(t)
 Dict{String,Any}("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
end
function save(path,x)
 ispath(path)&&error("existing output")
 open(path,"w") do io;TOML.print(io,x);end
end
@noinline function profile_batch(p,o,n)
 [plain(p,o) for _ in 1:n]
end
function case_run(::Type{T},f,out,nprofile) where T
 parse_start=time_ns();p=JSimplex.read_mps(joinpath(ROOT,f["path"]);value_type=T);parse_seconds=(time_ns()-parse_start)/1e9
 before=token(p);o=JSimplex.SolverOptions(T;algorithm=Symbol(f["algorithm"]),time_limit=10.0,iteration_limit=2000)
 c=Dict{String,Any}("id"=>f["id"],"scalar"=>string(T),"rows"=>size(p.A,1),"columns"=>size(p.A,2),"nnz"=>nnz(p.A),"parse_seconds"=>parse_seconds,"options"=>Dict(string(k)=>string(getfield(o,k)) for k in fieldnames(typeof(o))),"cold"=>Any[],"windows"=>Any[],"checks"=>Bool[])
 t=@timed plain(p,o);baseline=t.value;push!(c["cold"],merge(metrics(t),Dict("mode"=>"plain")))
 c["status"]=string(baseline.status);c["objective"]=string(baseline.objective_value);c["iterations"]=baseline.statistics.iterations;c["refactorizations"]=baseline.statistics.refactorizations
 oracle=baseline.status==JSimplex.OPTIMAL && !isnothing(baseline.objective_value) && isapprox(Float64(baseline.objective_value),f["expected"];rtol=1e-7,atol=1e-7)
 push!(c["checks"],oracle,token(p)==before)
 # Failure preserves the original status and ends this case without tuning/retry.
 if !oracle;save(joinpath(out,f["id"]*".toml"),c);error("baseline oracle failed") end
 base_sig=signature(baseline)
 d=JSimplex.SimplexDiagnostics(kernel_timing=true);t=@timed diagnosed(p,o,d)
 push!(c["cold"],merge(metrics(t),Dict("mode"=>"diagnosed")));push!(c["checks"],signature(t.value)==base_sig,token(p)==before)
 # One warm call per mode; profile_batch is also warmed outside sampling.
 warm=plain(p,o);wd=JSimplex.SimplexDiagnostics(kernel_timing=true);warmd=diagnosed(p,o,wd)
 warmbatch=profile_batch(p,o,1)
 push!(c["checks"],signature(warm)==base_sig,signature(warmd)==base_sig,signature(warmbatch[1])==base_sig,token(p)==before)
 for rep in 1:3
  for mode in (isodd(rep) ? ("plain","diagnosed") : ("diagnosed","plain"))
   diag=JSimplex.SimplexDiagnostics(kernel_timing=true)
   t=mode=="plain" ? (@timed plain(p,o)) : (@timed diagnosed(p,o,diag))
   w=merge(metrics(t),Dict("mode"=>mode,"rep"=>rep,"endpoint_equal"=>signature(t.value)==base_sig,"input_preserved"=>token(p)==before))
   if mode=="diagnosed"
    w["kernel_calls"]=Dict(string(k)=>v for (k,v) in diag.kernel_calls)
    w["kernel_seconds"]=Dict(string(k)=>Float64(v)/1e9 for (k,v) in diag.kernel_nanoseconds)
    w["event_counts"]=Dict(string(k)=>v for (k,v) in diag.counts)
   end
   push!(c["windows"],w)
  end
 end
 GC.gc();Profile.clear()
 pt=@timed Profile.@profile profile_batch(p,o,nprofile)
 c["profile"]=merge(metrics(pt),Dict("calls"=>nprofile,"buffer_full"=>Profile.is_buffer_full(),"endpoints_equal"=>all(s->signature(s)==base_sig,pt.value),"input_preserved"=>token(p)==before))
 data,lidict=Profile.retrieve(include_meta=false)
 frames=Dict(string(ip)=>[Dict("func"=>string(f.func),"file"=>string(f.file),"line"=>f.line,"from_c"=>f.from_c) for f in fs] for (ip,fs) in lidict)
 save(joinpath(out,f["id"]*"-stacks.toml"),Dict("data"=>string.(data),"frames"=>frames))
 save(joinpath(out,f["id"]*".toml"),c)
 all(c["checks"]) && all(w->w["endpoint_equal"]&&w["input_preserved"],c["windows"]) && c["profile"]["endpoints_equal"] && c["profile"]["input_preserved"] && !c["profile"]["buffer_full"] || error("correctness/profile gate")
 println("completed ",f["id"]," ",T," ",c["status"]," iterations=",c["iterations"])
 flush(stdout)
 nothing
end
function main()
 index=parse(Int,ARGS[1]);out=ARGS[2];ambient=precision(BigFloat);rnd=rounding(BigFloat)
 config=TOML.parsefile(joinpath(@__DIR__,"cases.toml"));T=index==1 ? Float64 : index==2 ? BigFloat : Q
 meta=Dict{String,Any}("index"=>index,"load_seconds"=>(time_ns()-LOAD_START)/1e9,"errors"=>String[])
 Profile.init(n=2_000_000,delay=0.001)
 Profile.@profile sum(1:100) # warm the sampling machinery, no solver work
 Profile.clear()
 try
  setprecision(BigFloat,256) do
   for f in config["cases"]
    index in f["stages"] || continue
    Base.inferencebarrier(case_run)(T,f,out,index==1 ? 64 : 8)
   end
  end
 catch e
  push!(meta["errors"],sprint(showerror,e,catch_backtrace()))
 finally
  meta["ambient_restored"]=precision(BigFloat)==ambient&&rounding(BigFloat)==rnd
  meta["loaded_paths"]=Dict(string(id)=>realpath(pathof(m)) for (id,m) in Base.loaded_modules if !isnothing(pathof(m)))
  save(joinpath(out,"raw.toml"),meta)
 end
 isempty(meta["errors"])||error("profile experiment failed")
end
Base.inferencebarrier(main)()
