using JSimplex, SparseArrays, TOML
problem=read_mps("/home/jspitz/mps/medium.mps")
rows=Dict{String,Any}[]
for algorithm in ("dual","primal")
    x=collect(reinterpret(Float64,read(joinpath(@__DIR__,"medium-highs-"*algorithm*"-primal.bin"))))
    a=problem.A*x
    records=Dict{String,Any}()
    for (label,values,lower,upper) in (("column",x,problem.column_lower,problem.column_upper),("row",a,problem.row_lower,problem.row_upper))
        largest=0.0;index=0;count_bad=0
        for i in eachindex(values)
            violation=max(JSimplex._lower_violation(lower[i],values[i]),JSimplex._upper_violation(upper[i],values[i]))
            if violation>largest;largest=violation;index=i;end
            count_bad+=violation>1e-7
        end
        records[label]=Dict{String,Any}("maximum_violation"=>largest,"index"=>index,"count_above_tolerance"=>count_bad)
        if index>0
            records[label]["value"]=values[index]
            records[label]["lower"]=string(lower[index]);records[label]["upper"]=string(upper[index])
            if label=="row"
                r=problem.A[index,:]
                exact=sum(Rational{BigInt}(r[j])*Rational{BigInt}(x[j]) for j in findnz(r)[1];init=zero(Rational{BigInt}))
                records[label]["exact_activity"]=string(exact)
            end
        end
    end
    records["algorithm"]=algorithm
    records["nonzero_coefficients_at_most_1e_9"]=count(v->0<abs(v)<=1e-9,nonzeros(problem.A))
    push!(rows,records);println(records);flush(stdout)
end
open(joinpath(@__DIR__,"medium-reference-check.toml"),"w") do io;TOML.print(io,Dict("cases"=>rows));end
