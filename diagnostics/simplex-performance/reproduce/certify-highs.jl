using JSimplex, LinearAlgebra, TOML, SHA
rows=Dict{String,Any}[]
for name in ("fast0507","runtime","medium")
    path="/home/jspitz/mps/"*name*".mps"
    problem=read_mps(path)
    for algorithm in ("dual","primal")
        binary=joinpath(@__DIR__,name*"-highs-"*algorithm*"-primal.bin")
        primal=collect(reinterpret(Float64,read(binary)))
        @assert length(primal)==size(problem.A,2)
        tolerance=SolverOptions().primal_tolerance
        valid=JSimplex._original_primal_feasible(problem,primal,tolerance)
        row=Dict("name"=>name,"algorithm"=>algorithm,"rows"=>size(problem.A,1),
            "columns"=>length(primal),"input_sha256"=>bytes2hex(open(sha256,path)),
            "solution_sha256"=>bytes2hex(open(sha256,binary)),
            "original_primal_certified"=>valid,"primal_tolerance"=>tolerance,
            "objective"=>dot(problem.objective,primal)+problem.objective_constant)
        push!(rows,row);println(row);flush(stdout)
        open(joinpath(@__DIR__,"highs-certificates.toml"),"w") do io;TOML.print(io,Dict("cases"=>rows));end
    end
end
