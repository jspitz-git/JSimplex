using JSimplex,LinearAlgebra,SparseArrays,TOML
const JS=JSimplex
@assert Threads.nthreads()==BLAS.get_num_threads()==1
Base.include(JS,joinpath(@__DIR__,"pipeline_support_baseline.jl"))
source=read(joinpath(dirname(pathof(JS)),"hypersparse_pipeline.jl"),String)
pos=only(findall("function _pipeline_output_support!(",source));candidate,_=Meta.parse(source,first(pos))
function probe(manager,variant)
    T=Float32;m=64;A=sparse(Matrix{T}(I,m,m).+T(1//1024));costs=zeros(T,m);costs[1:8].=-one(T)
    p=JS.LinearProblem(A,costs;row_upper=fill(T(10),m))
    o=JS.SolverOptions(T;algorithm=:primal,simplex_strategy=:legacy,pricing=:dantzig,
        basis_update=manager,basis_refactorization=:markowitz,partial_pricing=false,
        refactorization_interval=160,iteration_limit=100,verbose=false)
    policy=JS.NumericalPolicy(T;simplex_strategy=:legacy,hypersparse=true,refactor_timing=false)
    ws=JS.initialize_workspace(p,o;progress=JS.SimplexProgressContext(p;numerical_policy=policy))
    rows=Dict[]
    for i in 1:8
        result=JS._primal_iteration!(ws,()->false,o.dual_tolerance)
        row=Dict("step"=>i,"iterations"=>ws.iterations,"updates"=>length(ws.factorization.updates),
            "return"=>string(result),"primal_infeasibility"=>Float64(JS.primal_infeasibility(ws)),
            "dual_infeasibility"=>Float64(JS.dual_infeasibility(ws)))
        push!(rows,row);println(variant," ",manager," ",row);flush(stdout)
        isnothing(result)||break
    end
    Dict("variant"=>variant,"manager"=>string(manager),"steps"=>rows)
end
rows=Dict[]
for variant in ("control","candidate")
    if variant=="control"
        Core.eval(JS,:(_pipeline_output_support!(ws,cache,index,values,canonical::Bool)=_pipeline_original_output_support!(ws,cache,index,values)))
    else
        Core.eval(JS,candidate)
    end
    for manager in (:pfi,:huangfu_hall)
        push!(rows,Base.invokelatest(probe,manager,variant))
    end
end
open(io->TOML.print(io,Dict("cases"=>rows)),only(ARGS),"w")
