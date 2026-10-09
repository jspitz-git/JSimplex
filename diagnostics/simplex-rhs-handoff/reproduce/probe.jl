# Experimental unit-RHS handoff. Production code remains unchanged.
using JSimplex, SparseArrays, LinearAlgebra, Random, Statistics, TOML
const JS = JSimplex
function unit_solve!(destination, factor::JS.PFIFactorization{T}, rhs, p) where T
    destination === factor.work && error("Scratch alias")
    JS._check_rhs_dimension(factor,rhs); JS._check_destination_dimension(factor,destination)
    fill!(factor.work,zero(T)); factor.work[p]=one(T)
    for eta in Iterators.reverse(factor.updates)
        value=zero(T)
        for index in eachindex(eta.indices)
            value += eta.values[index]*factor.work[eta.indices[index]]
        end
        factor.work[eta.pivot_row]=value
    end
    JS._backend_transpose_solve!(destination,factor.base,factor.work)
end
function unit_solve!(destination,factor::JS.AbstractTriangularBasisFactorization{T},rhs,p) where T
    destination === factor.work && error("Scratch alias")
    JS._check_triangular_dimensions(factor,destination,rhs)
    JS._invalidate_prepared_destination!(factor,destination)
    order=JS._upper_order(factor.upper)
    fill!(factor.work,zero(T))
    if isnothing(order)
        factor.work[factor.positions[p]]=one(T)
        JS._upper_transpose_solve!(factor.work,factor.upper,JS._dense_upper_columns(factor))
        JS._finish_triangular_transpose!(destination,factor,nothing)
    else
        factor.work[order.order[factor.positions[p]]]=one(T)
        JS._stable_upper_transpose_solve!(factor.work,factor.upper,JS._dense_upper_columns(factor),order)
        JS._finish_triangular_transpose!(destination,factor,order)
    end
end
function unit_solve!(destination,f::JS.HuangfuHallFactorization{T},rhs,p) where T
    JS._hh_dimensions(destination,f,rhs)
    b=f.base; x=f.work
    fill!(x,zero(T)); x[b.positions[p]]=one(T)
    JS._hh_upper!(x,b,true)
    for t in Iterators.reverse(f.updates); JS._hh_apply!(x,t,true); end
    JS._hh_lower!(x,b,true)
    for i in eachindex(x)
        row=b.rows[i]
        destination[row]=b.divide_scaling ? x[i]/b.scaling[row] : x[i]*b.scaling[row]
    end
    destination
end
production!(out,f,rhs,p)=JS.transpose_solve!(out,f,JS._unit_transpose_rhs(f,rhs,p))
const CANDIDATE = length(ARGS)>1 && ARGS[2]=="production" ? production! : unit_solve!
baseline!(out,f,rhs,p)=JS.transpose_solve!(out,f,rhs)
# Include materializing the unchanged dense RHS, as required by existing residual checks.
function operation!(solve!,out,f,rhs,p)
    fill!(rhs,zero(eltype(rhs))); rhs[p]=one(eltype(rhs))
    solve!(out,f,rhs,p)
end
function batch!(solve!,out,f,rhs,p,count)
    start=time_ns()
    for _ in 1:count;operation!(solve!,out,f,rhs,p);end
    (time_ns()-start)/count
end
function measure(f,rhs,p)
    out=similar(rhs); ref=similar(rhs)
    operation!(baseline!,ref,f,rhs,p);operation!(CANDIDATE,out,f,rhs,p)
    @assert isequal(out,ref)
    for q in (1,length(rhs),max(1,p-5))
        operation!(baseline!,ref,f,rhs,q);operation!(CANDIDATE,out,f,rhs,q)
        @assert isequal(out,ref)
    end
    for _ in 1:4;batch!(baseline!,out,f,rhs,p,3);batch!(CANDIDATE,out,f,rhs,p,3);end
    estimate=batch!(baseline!,out,f,rhs,p,3)
    count=clamp(ceil(Int,2e7/max(estimate,1)),2,2000)
    a=Float64[];b=Float64[]
    for k in 1:11
        if isodd(k)
            push!(a,batch!(baseline!,out,f,rhs,p,count));push!(b,batch!(CANDIDATE,out,f,rhs,p,count))
        else
            push!(b,batch!(CANDIDATE,out,f,rhs,p,count));push!(a,batch!(baseline!,out,f,rhs,p,count))
        end
    end
    alloc_a=@allocated operation!(baseline!,out,f,rhs,p)
    alloc_b=@allocated operation!(CANDIDATE,out,f,rhs,p)
    Dict("baseline_ns"=>a,"unit_ns"=>b,"baseline_median_ns"=>median(a),"unit_median_ns"=>median(b),
         "baseline_bytes"=>alloc_a,"unit_bytes"=>alloc_b,"batch_count"=>count,"equal"=>true)
end
function main(path)
    results=Dict[]; rng=MersenneTwister(73194)
    for (shape,n) in (("dense",256),("sparse",20000),("wide_sparse",360982))
        original = shape=="dense" ? sparse(Matrix{Float64}(I,n,n)+rand(rng,n,n)/n) :
            spdiagm(-1=>fill(-0.1,n-1),0=>fill(2.0,n),1=>fill(0.125,n-1))[:,randperm(rng,n)]
        for (name,Factor) in (("pfi",JS.PFIFactorization),("ft",JS.ForrestTomlinFactorization),
                ("ss",JS.SuhlSuhlFactorization),("bg",JS.BartelsGolubFactorization),("hh",JS.HuangfuHallFactorization))
            B=copy(original); f=Factor(B); rhs=zeros(n); direction=zeros(n)
            for chain in (0,80,320)
                previous=chain==0 ? 0 : chain==80 ? 0 : 80
                for k in previous+1:chain
                    p=mod1(31k,n);q=mod1(p+17,n)
                    a=Vector(B[:,p])+0.01Vector(B[:,q])
                    JS.forward_solve!(direction,f,a);JS.replace_column!(f,direction,p)
                    B[:,p]=a
                end
                row=merge(Dict("shape"=>shape,"n"=>n,"manager"=>name,"chain"=>chain),measure(f,rhs,mod1(617,n)))
                push!(results,row)
                println(name," ",shape," ",chain," ratio=",row["unit_median_ns"]/row["baseline_median_ns"]," bytes=",row["unit_bytes"]);flush(stdout)
                open(path,"w") do io;TOML.print(io,Dict("candidate"=>string(CANDIDATE),"results"=>results));end
            end
        end
    end
end
main(ARGS[1])
