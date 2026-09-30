# A finite native-neighbor feasibility probe, not a proposed solver strategy.
using JSimplex, Serialization, SHA, TOML, SparseArrays
include(joinpath(@__DIR__,"joint_point_probe.jl"))
prefix,inspection,output=ARGS
ws=point_workspace(prefix*".bin")
point=deserialize(inspection*"-sweep_8.bin")
context=deserialize(inspection*"-context.bin")
ws.primal .= point
columns=[8507,8508]
rows=sort!(unique(vcat([ws.problem.A.rowval[collect(nzrange(ws.problem.A,j))] for j in columns]...)))
q(x)=Rational{BigInt}(x)
tol=ws.options.primal_tolerance
n=size(ws.problem.A,2)
records=Dict{String,Any}[]
exact_constants=Rational{BigInt}[]
coefficients=Vector{Rational{BigInt}}[]
row_limits=Tuple{Rational{BigInt},Rational{BigInt}}[]
for row in rows
    indices,values=findnz(ws.problem.A[row,:])
    constant=sum((q(a)*q(point[j]) for (j,a) in zip(indices,values) if j ∉ columns);init=q(0.0))
    a=[q(ws.problem.A[row,j]) for j in columns]
    value=constant+sum(a.*q.(point[columns]))
    lo,hi=context.row_lower[row],context.row_upper[row]
    rounded=Float64(value)
    margin=min(8eps(Float64)*max(tol,abs(clamp(rounded,lo,hi))),tol/4,(hi-lo)/4)
    push!(records,Dict("row"=>row,"basic_columns"=>[j for j in indices if ws.basis.states[j]==JSimplex.BASIC],"coefficients"=>Float64.(a),"constant"=>Float64(constant),
        "actual"=>Float64(value),"interval_lower"=>lo,"interval_upper"=>hi,
        "interior_lower"=>lo+margin,"interior_upper"=>hi-margin,
        "stored_activity"=>point[n+row],"activity_basic"=>ws.basis.states[n+row]==JSimplex.BASIC))
    # Finite equation limits intersect the actual working-model bounds.
    lower=q(point[n+row])-q(tol);upper=q(point[n+row])+q(tol)
    isfinite(ws.lower[n+row]) && (lower=max(lower,q(JSimplex.bound_value(ws.lower[n+row]))-q(tol)))
    isfinite(ws.upper[n+row]) && (upper=min(upper,q(JSimplex.bound_value(ws.upper[n+row]))+q(tol)))
    push!(exact_constants,constant);push!(coefficients,a);push!(row_limits,(lower,upper))
end
neighbor(x,k)=k<0 ? prevfloat(x,-k) : nextfloat(x,k)
found=Dict{String,Any}[]
for k in -16:16, l in -16:16
    values=[neighbor(point[columns[1]],k),neighbor(point[columns[2]],l)]
    all(context.lower[columns].<=values.<=context.upper[columns]) || continue
    feasible=all(eachindex(rows)) do i
        value=exact_constants[i]+sum(coefficients[i].*q.(values))
        row_limits[i][1]<=value<=row_limits[i][2]
    end
    feasible || continue
    ws.primal .= point;ws.primal[columns] .= values
    certified=JSimplex._legacy_primal_point_certified(ws)
    @assert certified
    @assert isequal(ws.primal[ws.basis.states.!=JSimplex.BASIC],point[ws.basis.states.!=JSimplex.BASIC])
    push!(found,Dict("offsets"=>[k,l],"values"=>values,"certified"=>certified,
        "maximum_change_from_stalled_point"=>maximum(abs.(values-point[columns]))))
    serialize(output*"-witness.bin",copy(ws.primal))
    break
end
# Exact necessary inequalities over all basic structural coordinates. This
# proves infeasibility only for the captured fixed nonbasic assignments.
row_lo,row_hi=25695,25697
basic_columns=findall(==(JSimplex.BASIC),ws.basis.states[1:n])
alo=[q(ws.problem.A[row_lo,j]) for j in basic_columns]
ahi=[q(ws.problem.A[row_hi,j]) for j in basic_columns]
@assert alo==ahi
@assert ws.basis.states[n+row_hi]!=JSimplex.BASIC
fixed(row)=sum((q(ws.problem.A[row,j])*q(point[j]) for j in 1:n
    if ws.basis.states[j]!=JSimplex.BASIC);init=q(0.0))
clo,chi=fixed(row_lo),fixed(row_hi)
required_lower=q(JSimplex.bound_value(ws.lower[n+row_lo]))-q(tol)-clo
required_upper=q(point[n+row_hi])+q(tol)-chi
gap=required_lower-required_upper
@assert gap>0
proof=Dict("lower_row"=>row_lo,"upper_row"=>row_hi,"same_basic_coefficients"=>true,
    "fixed_lower_constant"=>string(clo),"fixed_upper_constant"=>string(chi),
    "working_lower"=>JSimplex.bound_value(ws.lower[n+row_lo]),
    "fixed_upper_activity"=>point[n+row_hi],"tolerance"=>tol,
    "required_lower_exact"=>string(required_lower),"required_upper_exact"=>string(required_upper),
    "gap_exact"=>string(gap),"gap"=>Float64(gap))
pre=deserialize(prefix*"-before.bin")
nonbasic=ws.basis.states.!=JSimplex.BASIC
changed=findall(nonbasic .& (pre.primal .!= point))
ws.primal .= pre.primal
pre_feasible=JSimplex._legacy_primal_point_certified(ws)
@assert pre_feasible && changed==[8504]
transition=Dict("leaving"=>8504,"before_value"=>pre.primal[8504],"after_value"=>point[8504],
    "lower"=>JSimplex.bound_value(ws.lower[8504]),
    "retained_prepoint_certified_with_new_basis"=>pre_feasible,"changed_nonbasic_coordinates"=>changed,
    "scope"=>"Feasibility witness only; no altered pivot or solver continuation")
println("EXACT_CONTRADICTION ",proof);println("TRANSITION ",transition)
open(output,"w") do io
    TOML.print(io,Dict("scope"=>"Finite representable-neighbor probe within unchanged native intervals; exact checks are diagnostic only",
        "point_sha256"=>bytes2hex(open(sha256,inspection*"-sweep_8.bin")),
        "context_sha256"=>bytes2hex(open(sha256,inspection*"-context.bin")),
        "contradiction"=>proof,"transition"=>transition,
        "columns"=>columns,"initial_values"=>point[columns],"rows"=>records,"witnesses"=>found))
end
foreach(println,records);println("WITNESSES ",found)
