using JSimplex,SparseArrays,Serialization,Statistics,TOML,SHA
include("reference.jl")
include("prototype.jl")
separate!(out,ws,rho,row)=(JSimplex._csc_price!(out,ws.problem.A,rho);reference_ratio(ws,rho,row))
function sample(f,out,ws,rho,row,reps)
    f(out,ws,rho,row);GC.gc()
    @timed for _ in 1:reps;f(out,ws,rho,row);end
end
function main(root,path)
    @assert !ispath(path)
    records=[]
    for folder in sort(readdir(root;join=true))
        isdir(folder) || continue
        for file in sort(filter(f->endswith(f,".bin"),readdir(folder;join=true)))
            s=deserialize(file);A=s.A;m,n=size(A);out=zeros(eltype(A),m+n);other=similar(out)
            @assert length(unique(s.basics))==m && all(s.states[j]==JSimplex.BASIC for j in s.basics)
            @assert count(==(JSimplex.BASIC),s.states)==m
            ws=(;problem=(;A),basis=(;basic_indices=s.basics,states=s.states),options=(;zero_tolerance=s.tolerance),primal=out)
            a=separate!(out,ws,s.rho,s.row);b=combined!(other,ws,s.rho,s.row)
            @assert isequal(a,s.ratio) && isequal(a,b) && isequal(out,other)
            reps=max(2,min(100,5_000_000÷max(nnz(A),1)))
            old=[];new=[];oldbytes=[];newbytes=[]
            for round in 1:11
                for flag in (isodd(round) ? (false,true) : (true,false))
                    t=sample(flag ? combined! : separate!,out,ws,s.rho,s.row,reps)
                    @assert t.compile_time==0
                    push!(flag ? new : old,t.time/reps);push!(flag ? newbytes : oldbytes,t.bytes/reps)
                end
            end
            basic_nnz=sum(j<=n ? A.colptr[j+1]-A.colptr[j] : 0 for j in s.basics)
            r=Dict("case"=>basename(folder),"iteration"=>s.iteration,"offset"=>s.offset,"rows"=>m,"columns"=>n,"nonzeros"=>nnz(A),"basic_nonzeros"=>basic_nnz,"structural_basics"=>count(<=(n),s.basics),"nonzero_rho"=>count(!iszero,s.rho),"residual_ratio"=>a,"snapshot_sha256"=>bytes2hex(open(sha256,file)),"old_seconds"=>old,"new_seconds"=>new,"old_bytes"=>oldbytes,"new_bytes"=>newbytes,"ratio"=>median(new)/median(old),"repetitions"=>reps)
            push!(records,r);println(r["case"]," ",s.iteration," ratio=",r["ratio"]," old=",median(old)," new=",median(new));flush(stdout)
        end
    end
    open(path,"w") do io;TOML.print(io,Dict("cases"=>records));end
end
main(ARGS...)
