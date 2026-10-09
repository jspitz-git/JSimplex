using JSimplex,SparseArrays,Random,Statistics,TOML,SHA
include("reference.jl");include("prototype.jl")
separate!(out,ws,rho,row)=(JSimplex._csc_price!(out,ws.problem.A,rho);reference_ratio(ws,rho,row))
function sample(f,out,ws,rho,row,reps)
    f(out,ws,rho,row);GC.gc()
    @timed for _ in 1:reps;f(out,ws,rho,row);end
end
function main(path)
    @assert !ispath(path)
    records=Any[]
    for name in ("fast0507","runtime","medium","dense"),T in (Float32,Float64)
        A=name=="dense" ? sparse(randn(MersenneTwister(9),T,512,768)) : SparseMatrixCSC{T,Int}(read_mps("/home/jspitz/mps/"*name*".mps").A)
        m,n=size(A);rho=randn(MersenneTwister(17),T,m);out=zeros(T,m+n);other=similar(out)
        for fraction in (0.0,0.5,1.0)
            k=floor(Int,fraction*min(m,n));rng=MersenneTwister(19)
            basics=shuffle!(rng,[randperm(rng,n)[1:k];n.+randperm(rng,m)[1:m-k]])
            states=fill(JSimplex.AT_LOWER,m+n);states[basics].=JSimplex.BASIC
            ws=(;problem=(;A),basis=(;basic_indices=basics,states),options=(;zero_tolerance=T(1e-12)),primal=out)
            a=separate!(out,ws,rho,1);b=combined!(other,ws,rho,1)
            @assert isequal(a,b) && isequal(out,other)
            reps=max(2,min(100,2_000_000÷max(nnz(A),1)))
            old=[];new=[];oldbytes=[];newbytes=[]
            for round in 1:11
                for flag in (isodd(round) ? (false,true) : (true,false))
                    t=sample(flag ? combined! : separate!,out,ws,rho,1,reps)
                    @assert t.compile_time==0
                    push!(flag ? new : old,t.time/reps);push!(flag ? newbytes : oldbytes,t.bytes/reps)
                end
            end
            r=Dict("input"=>name,"type"=>string(T),"rows"=>m,"columns"=>n,"nonzeros"=>nnz(A),"structural_basics"=>k,"fraction"=>fraction,"old_seconds"=>old,"new_seconds"=>new,"old_bytes"=>oldbytes,"new_bytes"=>newbytes,"ratio"=>median(new)/median(old),"repetitions"=>reps)
            push!(records,r);println(name," ",T," ",fraction," ratio=",r["ratio"]," bytes=",median(oldbytes),"/",median(newbytes));flush(stdout)
        end
    end
    open(path,"w") do io;TOML.print(io,Dict("cases"=>records));end
end
main(only(ARGS))
