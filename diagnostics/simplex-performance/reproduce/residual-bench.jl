using JSimplex, SparseArrays, TOML
function measure(T, transposed)
    row = repeat(T[2^20,1,-2^20],100)
    B = sparse(transposed ? reshape(row,:,1) : reshape(row,1,:))
    x,rhs = ones(T,300),T[100]
    scratch,policy = JSimplex.SolveQualityScratch(T,1),JSimplex.NumericalPolicy(T)
    run() = JSimplex.solve_quality!(scratch,B,x,rhs,policy;transposed)
    @assert run().reliable
    samples = Dict{String,Any}[]
    for _ in 1:5
        GC.gc()
        result = @timed for _ in 1:1000; run(); end
        push!(samples,Dict("seconds"=>result.time,"bytes"=>result.bytes))
    end
    return Dict("type"=>string(T),"transposed"=>transposed,"calls"=>1000,"samples"=>samples)
end
report=Dict("source"=>pathof(JSimplex),"cases"=>[measure(T,t) for T in (Float32,Float64) for t in (false,true)])
open(ARGS[1],"w") do io; TOML.print(io,report); end
println(report)
