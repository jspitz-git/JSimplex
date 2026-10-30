# Usage: julia --project=. ratio_bench.jl baseline-primal_simplex.jl report.toml
using JSimplex, SparseArrays, Statistics, TOML, Test
module RatioBefore
using JSimplex: SimplexWorkspace, BASIC, AT_UPPER, AT_LOWER, bound_value,
    _upper_violation, _lower_violation, _primal_relaxed_step,
    _primal_bound_snap_feasible, _primal_step_bounds_feasible,
    _legacy_primal_row_validation_enabled, _primal_direction_magnitude
end
source=read(ARGS[1],String)
first=findfirst("function _primal_ratio(workspace::SimplexWorkspace{T}",source).start
last=findnext("function _legacy_primal_iteration!",source,first).start
include_string(RatioBefore,source[first:prevind(source,last)],ARGS[1])

function fixture(T,rows,dense)
    a=T[(dense || i%16==1) ? 1+(i%7)/8 : 0 for i in 1:rows]
    p=LinearProblem(sparse(reshape(a,:,1)),T[-1];row_upper=fill(T(2),rows))
    ws=JSimplex.initialize_workspace(p,SolverOptions(T;algorithm=:primal,verbose=false))
    return ws,-a
end
@noinline function repeated(f,ws,column,count)
    checksum=0
    for _ in 1:count
        result=f(ws,1,one(eltype(column)),column)
        checksum+=result[2]
    end
    checksum
end
function measure(f,ws,column,count)
    t=@timed repeated(f,ws,column,count)
    @assert t.compile_time==0
    Dict("seconds"=>t.time,"bytes"=>t.bytes,
         "allocations"=>Base.gc_alloc_count(t.gcstats),"checksum"=>t.value)
end
reports=Dict{String,Any}()
for T in (Float32,Float64), rows in (64,4096), dense in (false,true)
    ws,column=fixture(T,rows,dense)
    before,after=RatioBefore._primal_ratio,JSimplex._primal_ratio
    @test before(ws,1,one(T),column)==after(ws,1,one(T),column)
    count=rows==64 ? 8192 : 256
    for f in (before,after)
        repeated(f,ws,column,1)
        measure(f,ws,column,1)
    end
    old,new=Dict[],Dict[]
    for sample in 1:7
        if isodd(sample)
            push!(old,measure(before,ws,column,count))
            push!(new,measure(after,ws,column,count))
        else
            push!(new,measure(after,ws,column,count))
            push!(old,measure(before,ws,column,count))
        end
    end
    @test all(a["checksum"]==b["checksum"] for (a,b) in zip(old,new))
    reports["$(T)_$(rows)_$(dense ? "dense" : "sparse")"]=Dict(
        "calls_per_sample"=>count,"before"=>old,"after"=>new,
        "median_before_seconds"=>median(x["seconds"] for x in old),
        "median_after_seconds"=>median(x["seconds"] for x in new))
end
# Ordinary non-native arithmetic must retain its result and ownership behavior.
for T in (BigFloat,Rational{BigInt})
    ws,column=fixture(T,64,true)
    @test RatioBefore._primal_ratio(ws,1,one(T),column)==
          JSimplex._primal_ratio(ws,1,one(T),column)
end
open(ARGS[2],"w") do io
    TOML.print(io,reports;sorted=true)
end
println("Ratio measurements written to ",ARGS[2])
