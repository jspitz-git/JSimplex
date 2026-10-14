from pathlib import Path
import shutil,json
R=Path.cwd();B=R/'diagnostics/simplex-core-architecture/results';P=B/'PRESOLVE-EXACT-CACHE';D=B/'PRESOLVE-EXACT-CACHE-PIPELINE'
def write(p,s):
 with p.open('x') as f:f.write(s)
s=(P/'driver.jl').read_text();head=s[:s.index('function basic(')]
head=head.replace('include(joinpath(D,"cores.jl"))\nconst REF=CacheExperiment.reference_reduce\nconst CAND=CacheExperiment.candidate_reduce\n','')
synthetic=s[s.index('function synthetic('):s.index('@noinline batch')]
body='''@noinline presolve(p)=JSimplex.presolve_problem(p)
function cost_case(id,p)
 b=token(p);h=owners(p)
 t=@timed presolve(p);r=t.value;expected=token(r)
 rec=Dict{String,Any}("id"=>id,"side"=>SIDE,"cold"=>metrics(t),"signature"=>repr(expected),"cold_type"=>string(typeof(r)),"windows"=>Any[],"gc_warmup"=>Any[])
 rec["cold_input_preserved"]=preserved(p,b,h)
 for rep in 1:10
  if rep==4
   # Explicit untimed collection warms finalizer/GC paths; not an explanation
   # of the prior delayed compilation, and not part of steady-call throughput.
   g=@timed GC.gc();push!(rec["gc_warmup"],metrics(g))
  end
  t=@timed presolve(p)
  push!(rec["windows"],merge(metrics(t),Dict("rep"=>rep,"measured"=>rep>3,"outputs_equal"=>token(t.value)==expected,"input_preserved"=>preserved(p,b,h))))
 end
 save("presolve-"*id*".toml",rec)
 check(id,r isa JSimplex.PresolveResult && rec["cold_input_preserved"] && all(w->w["outputs_equal"]&&w["input_preserved"]&&(!w["measured"]||(w["compile_seconds"]==0&&w["recompile_seconds"]==0)),rec["windows"]))
end
function main()
 meta=Dict{String,Any}("index"=>INDEX,"side"=>SIDE,"load_seconds"=>(time_ns()-LOAD_START)/1e9,"errors"=>String[])
 ambient=(precision(BigFloat),rounding(BigFloat))
 try
  check("selected_package",realpath(pathof(JSimplex))==realpath(joinpath(OVERLAY,"src/JSimplex.jl")))
  method=which(JSimplex.reduce_dependent_rows,Tuple{LinearProblem{Float64}})
  meta["method_file"]=string(method.file);meta["method_line"]=method.line
  check("public_method_origin",realpath(string(method.file))==realpath(joinpath(OVERLAY,"src/presolve_dependencies.jl")))
  check("public_method_route",SIDE=="candidate" ? method.sig==Tuple{typeof(JSimplex.reduce_dependent_rows),LinearProblem{Float64}} : method.sig isa UnionAll)
  for f in TOML.parsefile(joinpath(D,"cases.toml"))["cases"]
   cost_case(f["id"],read_mps(joinpath(ROOT,f["path"]);value_type=Float64))
  end
  for kind in ("sparse","dense"), unique in (false,true)
   cost_case(kind*(unique ? "-unique" : "-repeated"),synthetic(kind,unique))
  end
 catch e
  push!(meta["errors"],sprint(showerror,e,catch_backtrace()))
 finally
  CHECKS["ambient_unchanged"]=(precision(BigFloat),rounding(BigFloat))==ambient
  meta["checks"]=CHECKS;meta["all_passed"]=isempty(meta["errors"])&&all(values(CHECKS))
  meta["loaded_paths"]=Dict(string(id)=>realpath(pathof(m)) for (id,m) in Base.loaded_modules if pathof(m)!==nothing)
  save("raw.toml",meta)
 end
 meta["all_passed"] || error("pipeline experiment failed; no retry")
 println("All ",length(CHECKS)," checks passed; eight whole-presolve cases.")
end
main()
'''
write(D/'driver.jl',head+synthetic+body)
for n in ('guard.py','cases.toml'):shutil.copyfile(P/n,D/n)
sup=(P/'supervisor.py').read_text().replace('started+84','started+64').replace('started+88','started+68').replace('started+90','started+70').replace('<=90','<=70');write(D/'supervisor.py',sup)
# New controls reuse only the pure host/review helpers; no previous script runs.
c=(P/'control.py').read_text().split('def stage_audit')[0];write(D/'control.py',c)
shutil.copyfile(__file__,D/'prepare.py')
print('New pipeline driver, unchanged cache and overlays; no numerical execution.')
