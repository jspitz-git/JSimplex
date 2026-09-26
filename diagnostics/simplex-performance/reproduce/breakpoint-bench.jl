using JSimplex, SparseArrays, Random, TOML
function measure(n,violation,repetitions)
    costs = Float64.(randperm(MersenneTwister(1507),n))
    ws = JSimplex.initialize_workspace(LinearProblem(spzeros(1,n),costs;
        column_upper=ones(n)),SolverOptions(verbose=false))
    row = [ones(n);0.0]
    run() = JSimplex._bound_flipping_ratio_test(ws,row,1.0,violation)
    run();run()
    samples=Dict{String,Any}[]
    for _ in 1:5
        GC.gc()
        r=@timed for _ in 1:repetitions;run();end
        push!(samples,Dict("seconds"=>r.time,"bytes"=>r.bytes))
    end
    return Dict("candidates"=>n,"violation"=>violation,"calls"=>repetitions,"samples"=>samples)
end
report=Dict("source"=>pathof(JSimplex),"cases"=>[
    measure(4096,0.5,1000),measure(4096,3.5,1000),measure(4096,5000.0,100),
    measure(63009,0.5,100)])
open(ARGS[1],"w") do io;TOML.print(io,report);end
println(report)
