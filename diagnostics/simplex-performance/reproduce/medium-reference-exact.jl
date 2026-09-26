using JSimplex, SparseArrays, TOML
problem=read_mps("/home/jspitz/mps/medium.mps")
records=Dict{String,Any}[]
for algorithm in ("dual","primal")
    x=collect(reinterpret(Float64,read(joinpath(@__DIR__,"medium-highs-"*algorithm*"-primal.bin"))))
    lo,hi=JSimplex._primal_row_bounds(problem.A,x,Val(false))
    rows=[i for i in eachindex(lo) if !JSimplex._primal_interval_within_bounds(lo[i],hi[i],problem.row_lower[i],problem.row_upper[i],1e-7)]
    slots=zeros(Int,size(problem.A,1));slots[rows]=1:length(rows)
    activities=zeros(Rational{BigInt},length(rows))
    for j in axes(problem.A,2)
        value=nothing
        for p in nzrange(problem.A,j)
            slot=slots[problem.A.rowval[p]];slot==0 && continue
            isnothing(value) && (value=Rational{BigInt}(x[j]))
            activities[slot]+=Rational{BigInt}(problem.A.nzval[p])*value
        end
    end
    maximum_violation=zero(Rational{BigInt});worst=0;bad_rows=Int[]
    for (slot,i) in enumerate(rows)
        a=activities[slot];lower=problem.row_lower[i];upper=problem.row_upper[i]
        violation=zero(Rational{BigInt})
        isfinite(lower) && (violation=max(violation,Rational{BigInt}(JSimplex.bound_value(lower))-a))
        isfinite(upper) && (violation=max(violation,a-Rational{BigInt}(JSimplex.bound_value(upper))))
        violation>Rational{BigInt}(1e-7) && push!(bad_rows,i)
        if violation>maximum_violation;maximum_violation=violation;worst=i;end
    end
    row=Dict{String,Any}("algorithm"=>algorithm,"ambiguous_rows"=>length(rows),"violating_rows"=>length(bad_rows),
        "first_violating_rows"=>bad_rows[1:min(10,end)],"maximum_exact_violation"=>string(maximum_violation),
        "maximum_exact_violation_float64"=>Float64(maximum_violation),"worst_row"=>worst,
        "column_certificate"=>JSimplex._within_primal_bounds(x,problem.column_lower,problem.column_upper,1e-7))
    push!(records,row);println(row);flush(stdout)
end
open(joinpath(@__DIR__,"medium-reference-exact.toml"),"w") do io;TOML.print(io,Dict("cases"=>records));end
