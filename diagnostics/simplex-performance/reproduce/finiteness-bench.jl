using JSimplex, SparseArrays, TOML
function measure(T,n)
    ws=JSimplex.initialize_workspace(LinearProblem(spzeros(T,0,n),zeros(T,n)),SolverOptions(T;verbose=false))
    run()=JSimplex._finite_workspace(ws)
    @assert run()
    samples=Dict{String,Any}[]
    for _ in 1:5
        GC.gc()
        r=@timed for _ in 1:1000;run();end
        push!(samples,Dict("seconds"=>r.time,"bytes"=>r.bytes))
    end
    return Dict("type"=>string(T),"size"=>n,"samples"=>samples)
end
report=Dict("source"=>pathof(JSimplex),"cases"=>[measure(T,n) for T in (Float32,Float64) for n in (63009,420526)])
open(ARGS[1],"w") do io;TOML.print(io,report);end
println(report)
