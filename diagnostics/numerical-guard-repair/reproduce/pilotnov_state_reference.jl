# Independent high-precision audit of the complete state at early growth events.
using JSimplex, LinearAlgebra, SparseArrays, Serialization, TOML
const JS=JSimplex
function main(directory,output)
    ispath(output) && error("Choose a fresh report")
    records=[]
    for iteration in (31,48,49,50,120,121,122,244,245,695)
        path=joinpath(directory,"pivot-$(iteration+1).bin")
        d=deserialize(path);m,n=size(d.problem.A);inds=d.basis.basic_indices
        record=setprecision(BigFloat,256) do
            A=hcat(BigFloat.(d.problem.A),-sparse(I,m,m));B=BigFloat.(d.B)
            x=BigFloat.(d.primal);nonbasic=copy(x);nonbasic[inds].=0
            factor=JS._factorize_basis(B,Val(:markowitz))
            basic=zeros(BigFloat,m);JS._backend_forward_solve!(basic,factor,-A*nonbasic)
            direction=zeros(BigFloat,m);JS._backend_forward_solve!(direction,factor,Vector(A[:,d.entering]))
            rhs=zeros(BigFloat,m);rhs[d.row]=1;rho=similar(rhs);JS._backend_transpose_solve!(rho,factor,rhs)
            stored=BigFloat.(d.direction)
            Dict("iteration"=>d.iteration,"pivot"=>d.pivot,
                "primal_maximum"=>maximum(abs,d.primal),"reference_basic_maximum"=>Float64(norm(basic,Inf)),
                "basic_relative_difference"=>Float64(norm(x[inds]-basic,Inf)/max(norm(basic,Inf),1)),
                "direction_relative_difference"=>Float64(norm(stored-direction,Inf)/max(norm(direction,Inf),1)),
                "rho_relative_difference"=>Float64(norm(BigFloat.(d.rho)-rho,Inf)/max(norm(rho,Inf),1)),
                "reference_next_basic_maximum"=>Float64(norm(basic-BigFloat(d.primal_step)*direction,Inf)),
                "stored_next_basic_maximum"=>Float64(norm(x[inds]-BigFloat(d.primal_step)*stored,Inf)),
                "reference_basis_residual"=>Float64(norm(B*basic+A*nonbasic,Inf)),
                "reference_direction_residual"=>Float64(norm(B*direction-A[:,d.entering],Inf)),
                "reference_row_residual"=>Float64(norm(transpose(B)*rho-rhs,Inf)))
        end
        push!(records,record);println(record);flush(stdout)
        open(output,"w") do io;TOML.print(io,Dict("records"=>records));end
    end
end
Base.invokelatest(main,ARGS...)
