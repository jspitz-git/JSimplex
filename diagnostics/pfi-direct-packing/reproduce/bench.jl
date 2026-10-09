using JSimplex, Statistics, TOML
const JS=JSimplex
Base.include(JS,joinpath(@__DIR__,"reference.jl"))
Base.include(JS,joinpath(@__DIR__,"prototype.jl"))
# Packing-only fixture: the backend provides a dimension, never a solve.
fixture(::Type{T},n) where T = JS.PFIFactorization{T,JS.UMFPACKBackend}(
    JS.UMFPACKBackend(nothing,n),JS.PackedEta{T}[],T[],JS.PackedEta{T}[],0,nothing)
function batch!(pack!,factor,column,pivot,recycle,reps)
    for _ in 1:reps
        pack!(factor,column,pivot)
        eta=pop!(factor.updates)
        recycle && push!(factor.recycled_updates,eta)
    end
end
function main(out,mode)
    @assert !ispath(out)
    candidate = mode=="prototype" ? JS.prototype_pack! : JS.replace_column!
    rows=Any[]
    for T in (Float32,Float64),n in (4132,20000,360982),density in ("sparse","dense"),recycle in (false,true)
        c=zeros(T,n);p=n÷2
        for i in (density=="dense" ? (1:n) : (1:97:n));c[i]=T((i%17)-8)/T(11);end
        c[p]=T(1.25)
        a=fixture(T,n);b=fixture(T,n)
        JS.reference_pack!(a,c,p);candidate(b,c,p)
        @assert a.updates[1].indices==b.updates[1].indices
        @assert isequal(a.updates[1].values,b.updates[1].values)
        empty!(a.updates);empty!(b.updates)
        reps=max(3,min(1000,2_000_000÷n))
        batch!(JS.reference_pack!,a,c,p,recycle,2);batch!(candidate,b,c,p,recycle,2)
        old=Float64[];new=Float64[];ob=Int[];nb=Int[]
        for sample in 1:11
            GC.gc()
            for which in (isodd(sample) ? (1,2) : (2,1))
                m=which==1 ? (@timed batch!(JS.reference_pack!,a,c,p,recycle,reps)) : (@timed batch!(candidate,b,c,p,recycle,reps))
                push!(which==1 ? old : new,m.time/reps)
                push!(which==1 ? ob : nb,m.bytes÷reps)
            end
        end
        row=Dict("type"=>string(T),"dimension"=>n,"density"=>density,"recycled"=>recycle,"nnz"=>count(!iszero,c),"repetitions"=>reps,"old_seconds"=>old,"new_seconds"=>new,"old_bytes"=>ob,"new_bytes"=>nb,"ratio"=>median(new)/median(old))
        push!(rows,row);println(T," ",n," ",density," recycled=",recycle," ratio=",row["ratio"]," bytes=",median(ob),"/",median(nb));flush(stdout)
    end
    open(out,"w") do io;TOML.print(io,Dict("cases"=>rows,"mode"=>mode));end
end
main(ARGS...)
