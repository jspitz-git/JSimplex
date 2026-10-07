using JSimplex,LinearAlgebra,SparseArrays,Serialization,TOML
const JS=JSimplex
function main(snapshot,output)
    ispath(output) && error("Choose a fresh report")
    d=deserialize(snapshot);ws=JS.initialize_workspace(d.problem,d.options);ws.basis=d.basis
    m=size(d.B,1);records=[]
    for bits in (256,512)
        record=setprecision(BigFloat,bits) do
            B=BigFloat.(d.B);rhs=zeros(BigFloat,m);rhs[d.row]=1;y=similar(rhs)
            result=Dict{String,Any}("bits"=>bits)
            elapsed=@elapsed try
                f=JS._factorize_basis(B,Val(:markowitz))
                JS._backend_transpose_solve!(y,f,rhs)
                result["absolute_residual"]=Float64(norm(transpose(B)*y-rhs,Inf))
                result["maximum"]=Float64(norm(y,Inf))
                result["rounded_ratio"]=JS._dual_row_residual_ratio(ws,Float64.(y),d.row)
                serialize(output*".$bits.bin",y)
            catch e
                result["exception"]=sprint(showerror,e)
            end
            result["seconds"]=elapsed
            result
        end
        push!(records,record);println(record);flush(stdout)
        open(output,"w") do io;TOML.print(io,Dict("checks"=>records));end
    end
end
Base.invokelatest(main,ARGS...)
