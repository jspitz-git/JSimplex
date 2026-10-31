# Small independent checks of diagnostic fidelity, not production changes.
include(joinpath(@__DIR__, "probe_failure2_reconstruction.jl"))
using JSimplex, SparseArrays, Serialization, TOML
for k in (1,6)
    A = spzeros(k+1,2k+1)
    for i in 1:k
        A[i,i]=A[i,k+i]=1.0
    end
    A[k+1,2k+1]=1.0
    p=LinearProblem(A,vcat(zeros(2k),1.0);row_lower=vcat(zeros(k),1.0),
        row_upper=vcat(zeros(k),nothing),column_upper=vcat(fill(0.01,2k),nothing))
    o=SolverOptions(algorithm=:primal,basis_update=:huangfu_hall,verbose=false,
        presolve=false,scaling=:off,iteration_limit=100)
    b=JSimplex.Basis(vcat(collect(1:k),3k+2),vcat(fill(JSimplex.BASIC,k),
        fill(JSimplex.AT_UPPER,k),fill(JSimplex.AT_LOWER,k+1),JSimplex.BASIC))
    target=vcat(zeros(k),fill(0.01,k),1.0)
    dir=mktempdir()
    input=joinpath(dir,"fixture.bin")
    serialize(input,(;problem=p,options=o,basis=b,target_primal=target,iterations=0,refactorizations=0))
    empty!(Failure2Diagnostics.events)
    Failure2Diagnostics.main(input,joinpath(dir,"trace"))
    report=TOML.parsefile(joinpath(dir,"trace.trace.toml"))
    @assert report["production_accepted"]
    @assert report["traced_matches_production_bitwise"]
    probe(joinpath(dir,"trace.before-reconstruction.bin"),joinpath(dir,"probe.toml"))
    detail=TOML.parsefile(joinpath(dir,"probe.toml"))
    @assert detail["combined_accepted"]
    @assert length(detail["combined_violations"])==k
    println("SMOKE PASS: ",k," violations")
end
