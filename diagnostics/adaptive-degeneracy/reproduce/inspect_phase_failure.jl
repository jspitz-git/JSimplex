using JSimplex, Serialization, LinearAlgebra, SparseArrays
BLAS.set_num_threads(1)
s = deserialize(ARGS[1])
p=s.problem; n=size(p.A,2); tolerance=s.options.primal_tolerance
viol=[max(JSimplex._lower_violation(s.lower[j],s.primal[j]),
          JSimplex._upper_violation(s.upper[j],s.primal[j])) for j in eachindex(s.primal)]
println("STATE iteration=",s.iterations," tolerance=",tolerance," step=",s.last_primal_step,
        " bound_max=",maximum(viol)," bound_count=",count(>(tolerance),viol))
for j in partialsortperm(viol,1:min(5,length(viol));rev=true)
 println("BOUND index=",j," row_activity=",j>n," basic=",s.basis.states[j]==JSimplex.BASIC,
    " value=",s.primal[j]," lower=",s.lower[j]," upper=",s.upper[j]," violation=",viol[j])
end
activities=p.A*s.primal[1:n]
errors=abs.(activities.-s.primal[n+1:end])
rows=unique(vcat(partialsortperm(errors,1:min(5,length(errors));rev=true),
    [j-n for j in eachindex(viol) if j>n && viol[j]>tolerance]))
slots=Dict(r=>i for (i,r) in enumerate(rows))
exact=zeros(Rational{BigInt},length(rows)); terms=zeros(Int,length(rows))
for col in axes(p.A,2), k in nzrange(p.A,col)
 slot=get(slots,p.A.rowval[k],0)
 slot==0 && continue
 exact[slot]+=Rational{BigInt}(p.A.nzval[k])*Rational{BigInt}(s.primal[col])
 terms[slot]+=1
end
for (slot,row) in enumerate(rows)
 error=exact[slot]-Rational{BigInt}(s.primal[n+row])
 println("ROW index=",row," terms=",terms[slot]," stored=",s.primal[n+row],
    " native_error=",errors[row]," exact_error=",Float64(error),
    " equation_feasible=",abs(error)<=Rational{BigInt}(tolerance),
    " exact_activity=",Float64(exact[slot])," lower=",s.lower[n+row]," upper=",s.upper[n+row],
    " working_row_feasible=",JSimplex._refined_primal_rows_feasible(p,s.primal[1:n],tolerance,[row],s.lower[n+1:end],s.upper[n+1:end]))
end
if hasproperty(s,:perturbations)
 j=s.perturbations
 println("PERTURBATION active=",JSimplex._has_active_bound_perturbations(j),
    " level=",isnothing(j)||isnothing(j.bounds) ? 0 : j.bounds.level)
end
