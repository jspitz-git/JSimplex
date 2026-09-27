using JSimplex, Serialization, SparseArrays, LinearAlgebra, TOML
function snapshot(f,B,rhs,destination)
    JSimplex.forward_solve!(destination,f,rhs)
    forward_residual=norm(B*destination-rhs,Inf)
    forward_scale=opnorm(B,Inf)*norm(destination,Inf)+norm(rhs,Inf)
    JSimplex.transpose_solve!(destination,f,rhs)
    transpose_residual=norm(transpose(B)*destination-rhs,Inf)
    transpose_scale=opnorm(B,1)*norm(destination,Inf)+norm(rhs,Inf)
    ft=minimum(@elapsed(for _ in 1:20;JSimplex.forward_solve!(destination,f,rhs);end) for _ in 1:3)/20
    bt=minimum(@elapsed(for _ in 1:20;JSimplex.transpose_solve!(destination,f,rhs);end) for _ in 1:3)/20
    entries=f isa JSimplex.PFIFactorization ? sum(length(u.values) for u in f.updates;init=0) :
        sum(JSimplex._update_storage_count,f.updates;init=0)
    return Dict{String,Any}("forward_seconds"=>ft,"transpose_seconds"=>bt,"history_entries"=>entries,
        "factor_entries"=>JSimplex._factor_storage_count(f),
        "forward_relative_residual"=>forward_residual/forward_scale,
        "transpose_relative_residual"=>transpose_residual/transpose_scale)
end
function warm(Factor)
    B=spdiagm(0=>ones(3));f=Factor(B)
    rhs=[1.0,0.25,0.0];direction=zeros(3)
    JSimplex.forward_solve!(direction,f,rhs)
    JSimplex.replace_column!(f,direction,1)
    JSimplex.transpose_solve!(direction,f,rhs)
    return nothing
end
function main()
    input,output=ARGS[1:2]
    data=deserialize(input);m,n=size(data.A)
    augmented=hcat(data.A,spdiagm(0=>-ones(m)))
    rows=Dict{String,Any}[]
    for Factor in (JSimplex.PFIFactorization,JSimplex.ForrestTomlinFactorization,
                   JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization)
        warm(Factor)
        indices=copy(data.basis);B=augmented[:,indices];f=Factor(B)
        rhs=ones(m);column=zeros(m);direction=zeros(m);out=zeros(m)
        update_seconds=0.0
        first_forward_seconds=0.0
        for (step,(row,entering)) in enumerate(data.steps)
            fill!(column,0.0)
            for p in augmented.colptr[entering]:(augmented.colptr[entering+1]-1)
                column[augmented.rowval[p]]=augmented.nzval[p]
            end
            JSimplex.forward_solve!(direction,f,column)
            update_seconds+=@elapsed JSimplex.replace_column!(f,direction,row)
            indices[row]=entering
            first_forward_seconds+=@elapsed JSimplex.forward_solve!(out,f,rhs)
            if step in (20,80,320)
                current_basis=augmented[:,indices]
                sample=snapshot(f,current_basis,rhs,out)
                fresh=Factor(current_basis)
                fresh_sample=snapshot(fresh,current_basis,rhs,out)
                sample["fresh_forward_seconds"]=fresh_sample["forward_seconds"]
                sample["fresh_transpose_seconds"]=fresh_sample["transpose_seconds"]
                sample["fresh_factor_entries"]=fresh_sample["factor_entries"]
                sample["fresh_forward_relative_residual"]=fresh_sample["forward_relative_residual"]
                sample["fresh_transpose_relative_residual"]=fresh_sample["transpose_relative_residual"]
                fresh=nothing
                sample["method"]=string(nameof(Factor));sample["updates"]=step
                sample["cumulative_update_seconds"]=update_seconds
                sample["cumulative_first_forward_seconds"]=first_forward_seconds
                push!(rows,sample);println(sample);flush(stdout)
                open(output,"w") do io;TOML.print(io,Dict("input"=>data.input,"input_sha256"=>data.input_sha256,"source"=>pathof(JSimplex),"julia"=>string(VERSION),"source_iteration"=>data.iteration,"rows"=>m,"columns"=>n,"samples"=>rows));end
            end
        end
        f=nothing;GC.gc()
    end
end
main()
