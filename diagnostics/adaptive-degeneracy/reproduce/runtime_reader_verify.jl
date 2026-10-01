# Verify returned points in a new process against a freshly read native model.
# Exact rational arithmetic is an independent diagnostic reference only.
using JSimplex,Serialization,SparseArrays,LinearAlgebra,TOML,SHA
BLAS.set_num_threads(1)
const Q=Rational{BigInt}
function maximum_violation(values,lower,upper)
    worst=Q(0);index=0
    for i in eachindex(values)
        below=isfinite(lower[i]) ? Q(bound_value(lower[i]))-values[i] : Q(0)
        above=isfinite(upper[i]) ? values[i]-Q(bound_value(upper[i])) : Q(0)
        violation=max(below,above)
        if violation>worst;worst=violation;index=i;end
    end
    worst,index
end
function verify(args)
    output=last(args);prefixes=args[1:end-1]
    path="/home/jspitz/mps/runtime.mps"
    @assert bytes2hex(open(sha256,path))=="d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68"
    p=read_mps(path);A=Q.(p.A);costs=Q.(p.objective)
    records=Dict{String,Any}[]
    for prefix in prefixes
        result=TOML.parsefile(prefix*".toml")
        result["status"]=="OPTIMAL" || continue
        point=deserialize(prefix*"-primal.bin").native_primal
        x=Q.(point);activity=A*x
        rv,ri=maximum_violation(activity,p.row_lower,p.row_upper)
        cv,ci=maximum_violation(x,p.column_lower,p.column_upper)
        tolerance=Q(result["primal_tolerance"])
        exact_objective=dot(costs,x)+Q(p.objective_constant)
        checked=max(rv,cv)<=tolerance
        certificate=JSimplex._original_primal_feasible(p,point,result["primal_tolerance"])
        row=Dict{String,Any}("reader"=>result["reader"],"algorithm"=>result["algorithm"],
            "exact_original_primal_feasible"=>checked,"native_certificate"=>certificate,
            "maximum_row_violation"=>Float64(rv),"maximum_column_violation"=>Float64(cv),
            "exact_maximum_row_violation"=>string(rv),"exact_maximum_column_violation"=>string(cv),
            "worst_row"=>ri,"worst_column"=>ci,"exact_objective"=>string(exact_objective),
            "objective_float64"=>Float64(exact_objective),"reported_objective"=>result["objective"])
        push!(records,row)
        println("VERIFIED ",row);flush(stdout)
        @assert checked && certificate
        @assert isapprox(Float64(exact_objective),result["objective"];rtol=1e-12,atol=1e-7)
    end
    open(output,"w") do io;TOML.print(io,Dict("records"=>records,"julia"=>string(VERSION)));end
end
verify(ARGS)
