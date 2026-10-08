using JSimplex, Serialization, SparseArrays, LinearAlgebra, TOML
const JS=JSimplex
function main(directory,output)
    ispath(output) && error("Choose a fresh report")
    records=[]
    for sequence in (50,122)
        d=deserialize(joinpath(directory,"ratio-$sequence.bin"));m,n=size(d.problem.A)
        r=setprecision(BigFloat,256) do
            A=hcat(BigFloat.(d.problem.A),-sparse(BigFloat.(Matrix{Float64}(I,m,m))))
            B=BigFloat.(d.B);f=JS._factorize_basis(B,Val(:markowitz))
            rho=zeros(BigFloat,m);unit=zeros(BigFloat,m);unit[d.row]=1
            JS._backend_transpose_solve!(rho,f,unit)
            y=zeros(BigFloat,m);JS._backend_transpose_solve!(y,f,BigFloat.(d.costs[d.basis.basic_indices]))
            prices=BigFloat.(d.costs)-transpose(A)*y;row=transpose(A)*rho
            x=BigFloat.(d.primal);nb=copy(x);nb[d.basis.basic_indices].=0
            basic=zeros(BigFloat,m);JS._backend_forward_solve!(basic,f,-A*nb)
            candidates=[]
            for entering in (d.entering,2156)
                dir=zeros(BigFloat,m);JS._backend_forward_solve!(dir,f,Vector(A[:,entering]))
                delta=basic[d.row]-BigFloat(JS.bound_value(d.orientation<0 ? d.lower[d.basis.basic_indices[d.row]] : d.upper[d.basis.basic_indices[d.row]]))
                step=delta/dir[d.row]
                next=basic-step*dir;next[d.row]=x[entering]+step
                push!(candidates,Dict("entering"=>entering,"stored_price"=>d.prices[entering],
                    "reference_price"=>Float64(prices[entering]),"reference_pivot"=>Float64(dir[d.row]),
                    "reference_oriented_ratio"=>Float64(prices[entering]/(d.orientation*row[entering])),
                    "reference_step"=>Float64(step),"next_basic_maximum"=>Float64(norm(next,Inf)),
                    "direction_relative_residual"=>Float64(norm(B*dir-A[:,entering],Inf)/max(norm(A[:,entering],Inf),1))))
            end
            Dict("iteration"=>d.iteration,"reference_basic_maximum"=>Float64(norm(basic,Inf)),
                "reference_basis_residual"=>Float64(norm(B*basic+A*nb,Inf)),
                "maximum_price_difference"=>Float64(norm(prices-BigFloat.(d.prices),Inf)),"candidates"=>candidates)
        end
        push!(records,r);println(r);flush(stdout)
        open(output,"w") do io;TOML.print(io,Dict("precision_bits"=>256,"records"=>records));end
    end
end
Base.invokelatest(main,ARGS...)
