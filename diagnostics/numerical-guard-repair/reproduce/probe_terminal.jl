using JSimplex,LinearAlgebra,SparseArrays,Serialization,TOML
const JS=JSimplex
function explain(d,y)
    p=d.problem;n=size(p.A,2);x=d.primal[1:n];o=d.options
    rl,ru=JS._original_reduced_cost_bounds(p,y)
    al,au=JS._primal_row_bounds(p.A,x,Val(false))
    failures=Dict{String,Any}[]
    for j in eachindex(rl)
        stationary=rl[j]>=-o.dual_tolerance && ru[j]<=o.dual_tolerance
        stationary && continue
        lo=j<=n ? p.column_lower[j] : p.row_lower[j-n]
        hi=j<=n ? p.column_upper[j] : p.row_upper[j-n]
        basic=d.basis.states[j]==JS.BASIC
        !basic && JS._is_fixed(lo,hi) && continue
        vl,vu=j<=n ? (x[j],x[j]) : (al[j-n],au[j-n])
        atlo=rl[j]>=-o.dual_tolerance && JS._primal_interval_at_bound(vl,vu,lo,o.primal_tolerance)
        athi=ru[j]<=o.dual_tolerance && JS._primal_interval_at_bound(vl,vu,hi,o.primal_tolerance)
        !basic && (atlo || athi) && continue
        exact_price=setprecision(BigFloat,256) do
            j<=n ? BigFloat(p.objective[j])-sum(BigFloat(p.A.nzval[k])*BigFloat(y[p.A.rowval[k]]) for k in nzrange(p.A,j);init=BigFloat(0)) : BigFloat(y[j-n])
        end
        push!(failures,Dict("index"=>j,"basic"=>basic,"price_lower"=>rl[j],"price_upper"=>ru[j],"price_256"=>Float64(exact_price),"activity_lower"=>vl,"activity_upper"=>vu,"lower"=>string(lo),"upper"=>string(hi)))
    end
    return Dict("certified"=>JS._original_witness_certified(p,o,d.basis,x,y),"primal_feasible"=>JS._original_primal_feasible(p,x,o.primal_tolerance),"failure_count"=>length(failures),"failures"=>failures[1:min(20,end)])
end
function main(snapshot,out)
    d=deserialize(snapshot);n=size(d.problem.A,2)
    rhs=[j<=n ? d.problem.objective[j] : 0.0 for j in d.basis.basic_indices]
    factor=lu(d.B);y=copy(d.dual);policy=JS.NumericalPolicy(Float64,d.options)
    scratch=JS.SolveQualityScratch(Float64,length(rhs));records=[]
    for k in 0:3
        r=explain(d,y);r["correction_count"]=k;push!(records,r)
        q=JS._compensated_solve_quality!(scratch,d.B,y,rhs,policy,true)
        r["basis_absolute_error"]=q.absolute_error
        k<3 && (y .+= transpose(factor)\scratch.residual)
    end
    result=Dict("snapshot"=>snapshot,"iteration"=>d.iteration,"offset"=>d.offset,"checks"=>records,"fresh_dual"=>explain(d,transpose(factor)\rhs))
    open(out,"w") do io;TOML.print(io,result;sorted=true);end
    println(result)
end
Base.invokelatest(main,ARGS...)
