using JSimplex,Test,LinearAlgebra,SparseArrays,TOML
BLAS.set_num_threads(1)
root=dirname(dirname(pathof(JSimplex)))
for name in ("primal_bound_snap_tests.jl","primal_candidate_retry_tests.jl")
    include(joinpath(root,"test",name)) do expr
        expr isa Expr && expr.head==:macrocall && expr.args[1]==Symbol("@testset") ? nothing : expr
    end
end
const Q=Rational{BigInt}
function exact_violation(values,lower,upper)
    worst=Q(0)
    for i in eachindex(values)
        isfinite(lower[i]) && (worst=max(worst,Q(bound_value(lower[i]))-values[i]))
        isfinite(upper[i]) && (worst=max(worst,values[i]-Q(bound_value(upper[i]))))
    end
    worst
end
records=Dict{String,Any}[]
for (name,ws) in (("sole_small_pivot",structural_bound_snap_workspace(0.01)),
    ("sole_unit_pivot",structural_bound_snap_workspace(1.0)),
    ("one_candidate",unsafe_structural_candidates(1)),
    ("two_candidates_without_safe_column",unsafe_structural_candidates(2;safe=false)),
    ("nine_candidates",unsafe_structural_candidates(9)))
    before=copy(ws.basis.basic_indices)
    terminal=JSimplex._primal_iteration!(ws,()->false,ws.options.dual_tolerance)
    p=ws.problem;n=size(p.A,2);x=ws.primal[1:n]
    row_violation=exact_violation(Q.(p.A)*Q.(x),p.row_lower,p.row_upper)
    column_violation=exact_violation(Q.(x),p.column_lower,p.column_upper)
    tolerance=Q(ws.options.primal_tolerance)
    push!(records,Dict("case"=>name,"before_basis"=>before,"after_basis"=>ws.basis.basic_indices,
        "terminal"=>isnothing(terminal) ? "continue" : string(terminal.status),
        "iterations"=>ws.iterations,"primal"=>x,
        "exact_row_violation"=>string(row_violation),"exact_column_violation"=>string(column_violation),
        "exact_original_feasible"=>max(row_violation,column_violation)<=tolerance,
        "original_certificate"=>JSimplex._original_primal_feasible(p,x,ws.options.primal_tolerance)))
end
@assert all(r->r["exact_original_feasible"] && r["original_certificate"],records)
open(only(ARGS),"w") do io;TOML.print(io,Dict("records"=>records));end
TOML.print(stdout,Dict("records"=>records))
