using TOML
s=read(joinpath(@__DIR__,"../results/S5-B/census-1-source.jl"),String)
s=first(split(s,"function main(out)"))
s=replace(s,"@assert result.status==NUMERICAL_ERROR"=>"println(\"ALIEN_STATUS \",algorithm,\"/\",profile,\" \",result.status,\" \",result.message)")
include_string(Main,s,"unchanged-census-probe")
rows=Any[]
for a in (:primal,:dual),p in (:native,:checked)
 row,_,_=run_case(Float64,a,:native,p,:bounds_alien,false);push!(rows,row)
end
open(only(ARGS),"w") do io;TOML.print(io,Dict("cases"=>rows));end
