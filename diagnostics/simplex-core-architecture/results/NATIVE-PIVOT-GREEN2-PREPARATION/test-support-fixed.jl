# UNEXECUTED diagnostic-only observation; no production method overrides.
module NP
using Test, JSimplex, SparseArrays, LinearAlgebra, TOML
const J=JSimplex
const counts=Dict{String,Int}()
const events=Vector{Dict{String,Any}}(undef,2048)
const used=Ref(0)
const output=ARGS[1]
need(x,s)=x || error(s)
token(x::Float64)=string(reinterpret(UInt64,x);base=16,pad=16)
scalar(x)=x isa Float64 ? token(x) : string(x)
# Always return dense text storage; never broadcast strings into sparse storage.
function dense_tokens(format, values::AbstractVector)
    result = Vector{String}(undef,length(values))
    for (i,value) in enumerate(values)
        result[i] = format(value)
    end
    return result
end
function state(f)
    b=hasproperty(f,:base) ? f.base : f
    if b isa J.UMFPACKBackend
        a=b.factorization;s=b.spare
        return Dict{String,Any}("kind"=>"UMFPACKBackend","backend"=>string(objectid(b)),"policy"=>string(b.pivot_policy),"dimension"=>b.dimension,
            "active"=>a===nothing ? "none" : string(objectid(a)),"spare"=>s===nothing ? "none" : string(objectid(s)),
            "control_owner"=>a===nothing ? "none" : string(objectid(a.control)),"control"=>a===nothing ? String[] : token.(a.control),
            "spare_control"=>s===nothing ? String[] : token.(s.control),"shared"=>b.shared,
            "updates"=>hasproperty(f,:updates) ? length(f.updates) : 0)
    end
    return Dict{String,Any}("kind"=>string(typeof(f)))
end
function observe(name,f,args...;kwargs...)
    counts[name]=get(counts,name,0)+1
    used[]+=1;need(used[]<=length(events),"Observation budget")
    e=Dict{String,Any}("call"=>name,"number"=>counts[name],"exception"=>"")
    events[used[]]=e
    !isempty(args) && (e["before"]=state(args[1]))
    try
        value=f(args...;kwargs...)
        e["after"]=state(value)
        if name in ("forward_solve","transpose_solve")
            e["output"]=dense_tokens(scalar,value)
            e["rhs"]=dense_tokens(scalar,args[2])
        end
        return value
    catch error
        e["exception"]=string(typeof(error))
        !isempty(args) && (e["after_failure"]=state(args[1]))
        rethrow()
    end
end
_factorize_basis(args...;kwargs...)=observe("_factorize_basis",J._factorize_basis,args...;kwargs...)
_basis_factorization(args...;kwargs...)=observe("_basis_factorization",J._basis_factorization,args...;kwargs...)
PFIFactorization(args...;kwargs...)=observe("PFIFactorization",J.PFIFactorization,args...;kwargs...)
ForrestTomlinFactorization(args...;kwargs...)=observe("ForrestTomlinFactorization",J.ForrestTomlinFactorization,args...;kwargs...)
SuhlSuhlFactorization(args...;kwargs...)=observe("SuhlSuhlFactorization",J.SuhlSuhlFactorization,args...;kwargs...)
BartelsGolubFactorization(args...;kwargs...)=observe("BartelsGolubFactorization",J.BartelsGolubFactorization,args...;kwargs...)
UMFPACKBackend(args...;kwargs...)=observe("UMFPACKBackend",J.UMFPACKBackend,args...;kwargs...)
refactorize!(args...;kwargs...)=observe("refactorize",J.refactorize!,args...;kwargs...)
_refactorize_backend(args...;kwargs...)=observe("_refactorize_backend",J._refactorize_backend,args...;kwargs...)
copy_basis_factorization(args...;kwargs...)=observe("copy_basis_factorization",J.copy_basis_factorization,args...;kwargs...)
replace_column!(args...;kwargs...)=observe("replace_column",J.replace_column!,args...;kwargs...)
forward_solve(args...;kwargs...)=observe("forward_solve",J.forward_solve,args...;kwargs...)
transpose_solve(args...;kwargs...)=observe("transpose_solve",J.transpose_solve,args...;kwargs...)
hypersparse_forward_solve!(args...;kwargs...)=observe("hypersparse_forward_solve",J.hypersparse_forward_solve!,args...;kwargs...)
hypersparse_transpose_solve!(args...;kwargs...)=observe("hypersparse_transpose_solve",J.hypersparse_transpose_solve!,args...;kwargs...)
sparse_solve_view(args...;kwargs...)=observe("sparse_solve_view",J.sparse_solve_view,args...;kwargs...)
raw_lu(args...;kwargs...)=observe("raw_lu",lu,args...;kwargs...)
const equations=Vector{Dict{String,Any}}(undef,400)
const equation_count=Ref(0)
function equation!(matrix,rhs,x,trans)
    equation_count[]+=1;need(equation_count[]<=length(equations),"Equation budget")
    B=sparse(matrix)
    equations[equation_count[]]=Dict("matrix"=>Dict("n"=>size(B,1),"colptr"=>copy(B.colptr),"rowval"=>copy(B.rowval),"nzval"=>token.(B.nzval)),"rhs"=>dense_tokens(token,rhs),"output"=>dense_tokens(token,x),"transposed"=>trans)
    nothing
end
end # module
