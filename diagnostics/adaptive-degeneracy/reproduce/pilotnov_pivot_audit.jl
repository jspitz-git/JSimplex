# Observe fresh factorization around accepted dual pivots; do not alter decisions.
using JSimplex,LinearAlgebra,SparseArrays,Serialization,SHA,TOML
const PIVOT_AUDITS=Dict{String,Any}[]
const BAD_PIVOT_JOBS=Set{String}()
function fresh_status(B)
    try
        JSimplex._factorize_basis(B,Val(:native));return "success"
    catch e
        JSimplex._is_numerical_exception(e) || rethrow()
        return sprint(showerror,e)
    end
end
function audit_pilotnov_pivot(ws,entering,leaving,direction)
    B=JSimplex.basis_matrix(ws);rhs=zeros(size(B,1))
    JSimplex._pivot_column!(rhs,ws,entering)
    nextB=copy(B);nextB[:,leaving]=rhs
    current=fresh_status(B);proposed=fresh_status(nextB)
    prefix=Main.CAPTURE_PREFIX[]
    record=Dict{String,Any}("prefix"=>prefix,"iteration"=>ws.iterations,
        "entering"=>entering,"leaving"=>leaving,"pivot"=>direction[leaving],
        "row_coefficient"=>ws.scratch.tableau_row[entering],
        "maximum_direction"=>maximum(abs,direction),"current_factorization"=>current,
        "proposed_factorization"=>proposed)
    if proposed!="success" && !(prefix in BAD_PIVOT_JOBS)
        push!(BAD_PIVOT_JOBS,prefix)
        path=prefix*"-first-unfactorable-pivot.bin"
        serialize(path,(;B,nextB,rhs,direction=copy(direction),rho=copy(ws.scratch.rho),
            entering,leaving,iteration=ws.iterations,tableau_coefficient=ws.scratch.tableau_row[entering]))
        record["snapshot"]=path
        Main.detach(ws,prefix*"-before-unfactorable-pivot.bin")
    end
    push!(PIVOT_AUDITS,record)
end
source=read(joinpath(dirname(pathof(JSimplex)),"dual_simplex.jl"),String)
needle="    _replace_pivot_column!(workspace, tableau_column, leaving_row;"
@assert count(needle,source)==1
source=replace(source,needle=>"    Main.audit_pilotnov_pivot(workspace,entering_index,leaving_row,tableau_column)\n"*needle)
const PIVOT_AUDIT_SHA256=bytes2hex(sha256(source))
Base.include_string(JSimplex,source,"diagnostic_dual_pivot_audit.jl")
include(joinpath(@__DIR__,"broad_without_presolve.jl"))
open(ARGS[4]*"-pivots.toml","w") do io
    TOML.print(io,Dict("instrumentation_sha256"=>PIVOT_AUDIT_SHA256,"records"=>PIVOT_AUDITS))
end
