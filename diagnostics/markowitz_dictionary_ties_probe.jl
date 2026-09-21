# Reuses only the process-local prototype definitions from the main comparison.
initialization = first(split(read("diagnostics/markowitz_dictionary_probe.jl",String),
    "\nrows=Dict{String,Any}[]"))
Base.include_string(Main,initialization,"dictionary-probe-initialization.jl")
using Random
cases=Dict{String,Any}[]
@testset "Equal-magnitude pivot ties after dictionary history" begin
    for seed in 1:40
        n=32; rng=MersenneTwister(seed)
        B=spdiagm(0=>ones(n))
        for i in 1:n, offset in (1,5,13)
            B[i,mod1(i+offset,n)] = rand(rng,Bool) ? 1.0 : -1.0
        end
        abs(det(Matrix(B))) > 1e-6 || continue
        empty!(JSimplex.dictionary_probe_cache)
        f=JSimplex.PFIFactorization(B,Val(:markowitz))
        cold=metadata(f,B)
        for _ in 1:3; JSimplex.refactorize!(f,B); end
        warm=metadata(f,B)
        JSimplex.refactorize!(f,matrix_case(Float64,n,"history"))
        for _ in 1:3; JSimplex.refactorize!(f,B); end
        history=metadata(f,B)
        push!(cases,Dict("seed"=>seed,"cold"=>cold,"warm"=>warm,"history"=>history,
            "cold_matches_warm"=>cold["row_order"]==warm["row_order"] && cold["column_order"]==warm["column_order"],
            "warm_matches_history"=>warm["row_order"]==history["row_order"] && warm["column_order"]==history["column_order"]))
    end
end
open(io->TOML.print(io,Dict("mode"=>mode,"cases"=>cases);sorted=true),ARGS[2],"w")
println(mode," changed after same-matrix warm: ",count(c->!c["cold_matches_warm"],cases),
    "; changed after denser history: ",count(c->!c["warm_matches_history"],cases)," / ",length(cases))
