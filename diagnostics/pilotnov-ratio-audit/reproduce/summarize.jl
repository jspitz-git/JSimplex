using JSimplex, Serialization, TOML, LinearAlgebra
const JS=JSimplex
function main(directory,output)
    ispath(output) && error("Choose a fresh report")
    records=[]
    paths=filter(p->startswith(basename(p),"ratio-") && endswith(p,".bin"),readdir(directory;join=true))
    sort!(paths;by=p->parse(Int,match(r"ratio-(\d+)",p)[1]))
    for path in paths
        d=deserialize(path);tol=d.options.dual_tolerance;cutoff=JS._dual_pivot_cutoff(Float64)
        candidates=[]
        for j in eachindex(d.tableau)
            c=d.orientation*d.tableau[j];state=d.basis.states[j]
            JS._is_fixed(d.lower[j],d.upper[j]) && continue
            ((state==JS.AT_LOWER && c>cutoff)||(state==JS.AT_UPPER && c < -cutoff)||(state==JS.FREE_NONBASIC && abs(c)>cutoff)) || continue
            push!(candidates,(index=j,coefficient=c,price=d.prices[j],step=d.prices[j]/c,
                relaxed=(d.prices[j]+copysign(tol,c))/c,state=string(state),
                lower=isfinite(d.lower[j]) ? JS.bound_value(d.lower[j]) : -Inf,
                upper=isfinite(d.upper[j]) ? JS.bound_value(d.upper[j]) : Inf))
        end
        isempty(candidates) && continue
        limit=minimum(c.relaxed for c in candidates if isfinite(c.relaxed);init=Inf)
        eligible=filter(c->c.step<=limit && !(c.index in d.rejected),candidates)
        h=isempty(eligible) ? nothing : eligible[argmax(abs(c.coefficient) for c in eligible)]
        chosen=d.entering>0 ? d.tableau[d.entering] : NaN
        r=Dict("snapshot"=>basename(path),"iteration"=>d.iteration,"entering"=>d.entering,"row"=>d.row,
            "delta"=>d.delta,"orientation"=>d.orientation,"primal_maximum"=>norm(d.primal,Inf),
            "coefficient"=>chosen,"coefficient_relative"=>abs(chosen)/norm(d.tableau,Inf),
            "step"=>d.entering>0 ? d.prices[d.entering]/(d.orientation*chosen) : NaN,
            "flips"=>length(d.flips),"harris_limit"=>limit,"tableau_maximum"=>norm(d.tableau,Inf))
        if !isnothing(h)
            r["harris_index"]=h.index;r["harris_coefficient"]=h.coefficient;r["harris_step"]=h.step
        end
        if d.iteration in (0,1,2,30,31,32,47,48,49,50,119,120,121,122,243,244,245,694,695,696)
            sort!(candidates;by=c->(c.step,c.index))
            r["first_candidates"]=[Dict(string(k)=>getproperty(c,k) for k in propertynames(c)) for c in candidates[1:min(12,length(candidates))]]
        end
        push!(records,r)
    end
    open(output,"w") do io;TOML.print(io,Dict("records"=>records));end
    for r in records
        if r["iteration"] in (0,1,2,30,31,32,47,48,49,50,119,120,121,122,243,244,245,694,695,696)
            println(filter(p->p.first!="first_candidates",r))
        end
    end
end
Base.invokelatest(main,ARGS...)
