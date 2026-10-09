using JSimplex,Test,SparseArrays,LinearAlgebra
# Deliberately corrupt one contract in this process only. A nonzero test exit
# is expected; no source file or persistent solver method is changed on disk.
root=dirname(dirname(pathof(JSimplex)))
mode=only(ARGS)
file,target = mode == "snap" ? ("simplex.jl","_can_preserve_primal_bound_value") :
    mode == "sum" ? ("primal_simplex.jl","_primal_bound_snap_feasible") : error("Unknown mutation")
expressions=filter(ex->ex isa Expr && ex.head==:function && occursin(target,string(ex.args[1])),
    Meta.parseall(read(joinpath(root,"src",file),String)).args)
@assert length(expressions)==1
ex=only(expressions)
if mode=="snap"
    ex.args[2]=:(return false)
else
    old="violation = max(violation, bound_violation)"
    source=string(ex)
    @assert occursin(old,source)
    ex=Meta.parse(replace(source,old=>"violation += bound_violation"))
end
Core.eval(JSimplex,ex)
@testset "Deliberately broken $mode contract" begin
 include(joinpath(root,"test/primal_bound_snap_tests.jl"))
 include(joinpath(root,"test/primal_candidate_retry_tests.jl"))
end
