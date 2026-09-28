using JSimplex,Serialization,LinearAlgebra,SparseArrays,Logging
const J=JSimplex
include("intervention.jl")
function inspect(path)
    d=deserialize(path);ws=J.initialize_workspace(d.problem,d.options)
    ws.basis=deepcopy(d.basis);ws.costs.=d.costs;ws.lower.=d.lower;ws.upper.=d.upper;ws.primal.=d.primal
    ws.iterations=d.iteration;ws.factorization=d.factorization
    J._validate_basis(ws)
    B=copy(J._basis_matrix!(ws));buffers=J._pivot_quality_buffers(ws)
    rhs=copy(J._pivot_column!(buffers.rhs,ws,d.entering));col=copy(d.direction)
    q=J._compensated_solve_quality!(buffers.column,B,col,rhs,ws.progress.numerical_policy,false)
    println("CAPTURE metadata=",d.metadata," row=",d.row," pivot=",col[d.row]," quality=",q)
    println("ROW relative_agreement=",abs(col[d.row]-d.tableau[d.entering])/abs(col[d.row])," row_residual=",J._dual_row_residual_ratio(ws,d.rho,d.row))
    isnothing(q) && error("Unavailable native residual")
    residual=copy(buffers.column.residual)
    correction=zeros(length(col));J._ordinary_forward_solve!(correction,ws.factorization,residual)
    corrected=col+correction
    println("NATIVE correction_inf=",norm(correction,Inf)," pivot_correction=",correction[d.row]," relative_pivot_correction=",abs(correction[d.row]/col[d.row])," corrected_pivot=",corrected[d.row])
    q2=J._compensated_solve_quality!(buffers.column,B,corrected,rhs,ws.progress.numerical_policy,false)
    println("CORRECTED_QUALITY ",q2)
    scale=abs.(B)*abs.(col)+abs.(rhs)
    ratios=[iszero(scale[i]) ? 0.0 : abs(residual[i])/scale[i] for i in eachindex(scale)]
    for i in sortperm(ratios;rev=true)[1:8]
        println("RESIDUAL_ROW row=",i," residual=",residual[i]," scale=",scale[i]," ratio=",ratios[i]," rhs=",rhs[i]," col=",col[i])
    end
    # Diagnostic reference: 256-bit residuals, corrections using the saved Float64 factor.
    # This does not construct an independent high-precision factorization.
    setprecision(BigFloat,256) do
        BB=BigFloat.(B);aa=BigFloat.(rhs);x=BigFloat.(col)
        for k in 1:8
            r=aa-BB*x
            c=zeros(length(col));J._ordinary_forward_solve!(c,ws.factorization,Float64.(r))
            x .+= BigFloat.(c)
            println("REFERENCE k=",k," residual_inf=",norm(aa-BB*x,Inf)," pivot=",x[d.row])
        end
        println("REFERENCE_FINAL relative_pivot_error=",abs((BigFloat(col[d.row])-x[d.row])/x[d.row])," direction_error_inf=",norm(BigFloat.(col)-x,Inf))
    end
end
with_logger(NullLogger()) do
    inspect(ARGS[1])
end
