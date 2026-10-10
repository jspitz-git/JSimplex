include("hooks.jl")
push!(HOOKS,(:refactorize!,"huangfu_hall_factorization.jl"))
const LABELS=vcat(["outer_unattributed","observer"],string.(first.(HOOKS)))
@eval JS begin
 const _tb_stats=zeros(Int64,128,9)
 const _tb_child=zeros(Int64,128,4)
 const _tb_depth=Ref(0)
 function _tb_begin()
  d=(_tb_depth[]+=1);@assert d<=128
  for j in 1:4;_tb_child[d,j]=0;end
  (Base.gc_num(),time_ns(),d)
 end
 function _tb_end(id,token)
  g,t,d=token;ns=Int64(time_ns()-t);delta=Base.GC_Diff(Base.gc_num(),g)
  values=(ns,delta.allocd,Base.gc_alloc_count(delta),delta.total_time)
  _tb_stats[id,1]+=1
  for j in 1:4
   _tb_stats[id,1+j]+=values[j]
   _tb_stats[id,5+j]+=values[j]-_tb_child[d,j]
   d>1 && (_tb_child[d-1,j]+=values[j])
  end
  _tb_depth[]-=1;nothing
 end
 function _tb_reset()
  @assert _tb_depth[]==0
  fill!(_tb_stats,0);fill!(_tb_child,0)
 end
 Base.@noinline function _tb_empty()
  t=_tb_begin();try;nothing;finally;_tb_end(1,t);end
 end
end
function install_hooks()
 for (i,(name,file)) in enumerate(HOOKS)
  source=read(joinpath(dirname(pathof(JS)),file),String)
  position=findfirst("function "*string(name)*"(",source);@assert !isnothing(position)
  ex,_=Meta.parse(source,first(position));body=ex.args[2];token=gensym(:token)
  ex.args[2]=quote
   local $token=_tb_begin()
   try;$body;finally;_tb_end($(i+2),$token);end
  end
  Core.eval(JS,ex)
 end
end
function counter_rows()
 s=JS._tb_stats
 [Dict("function"=>LABELS[i],"calls"=>s[i,1],"inclusive_seconds"=>s[i,2]/1e9,
 "inclusive_bytes"=>s[i,3],"inclusive_allocations"=>s[i,4],"inclusive_gc_seconds"=>s[i,5]/1e9,
 "exclusive_seconds"=>s[i,6]/1e9,"exclusive_bytes"=>s[i,7],"exclusive_allocations"=>s[i,8],
 "exclusive_gc_seconds"=>s[i,9]/1e9) for i in eachindex(LABELS) if s[i,1]>0]
end
function calibration()
 JS._tb_empty();records=[]
 for _ in 1:5
  t=@timed for _ in 1:10000;JS._tb_empty();end
  push!(records,Dict("seconds_per_probe"=>t.time/10000,"bytes"=>t.bytes,"compile_seconds"=>t.compile_time))
 end
 JS._tb_reset();outer=JS._tb_begin()
 try
  inner=JS._tb_begin()
  try;error("synthetic unwind");catch;finally;JS._tb_end(2,inner);end
 finally;JS._tb_end(1,outer);end
 @assert JS._tb_depth[]==0 && JS._tb_stats[1,1]==JS._tb_stats[2,1]==1
 @assert sum(JS._tb_stats[:,6])==JS._tb_stats[1,2]
 @assert sum(JS._tb_stats[:,7])==JS._tb_stats[1,3]
 JS._tb_reset();records
end
