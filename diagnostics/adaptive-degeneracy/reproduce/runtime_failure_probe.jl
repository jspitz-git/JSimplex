using JSimplex, Serialization, LinearAlgebra, SparseArrays
BLAS.set_num_threads(1)
const JS=JSimplex
for reader in ("native","jump")
 ws=deserialize(".superpowers/adaptive-degeneracy/runtime-reader-full/"*reader*"-dual-final.bin")
 ws.progress=JS.SimplexProgressContext(ws.problem;numerical_policy=ws.progress.numerical_policy,scaling=ws.progress.scaling)
 journal=ws.scratch.perturbations
 isnothing(journal) || (journal.workspace_id=objectid(ws))
 println("DUAL ",reader," perturbed=",ws.perturbed," journal=",isnothing(journal) ? nothing : (journal.active,journal.level)," updates=",length(ws.factorization.updates))
 bad=findall(i->ws.basis.states[i]!=JS.BASIC && !JS._is_fixed(ws.lower[i],ws.upper[i]) && !JS._dual_price_feasible(ws.basis.states[i],ws.reduced_costs[i],ws.options.dual_tolerance),eachindex(ws.costs))
 B=JS.basis_matrix(ws);factor=lu(B)
 high=JS._refined_dual_prices(ws,factor,B,256,()->false)
 for i in bad
  println("BAD index=",i," state=",ws.basis.states[i]," price=",ws.reduced_costs[i]," exact_reference=",isnothing(high) ? nothing : high[i]," cost=",ws.costs[i]," original=",i<=size(ws.problem.A,2) ? ws.problem.objective[i] : 0," journal_original=",isnothing(journal) ? nothing : journal.original_costs[i])
 end
 println("SHIFT ",JS._shift_marginal_dual_prices!(ws,()->false))
end
c=deserialize(".superpowers/adaptive-degeneracy/runtime-reader-full/jump-primal-component-1.bin")
x=copy(c.x);s=JS.SolveQualityScratch(Float64,length(c.rhs));rows=copy(transpose(c.B))
function quality(label,x,c,s)
 q=JS._compensated_solve_quality!(s,c.B,x,c.rhs,c.policy,false)
 bad=findall(i->abs(s.residual[i])>c.policy.solve_tolerance*s.work_scale[i],eachindex(c.rhs))
 println(label," reliable=",q.reliable," bad=",length(bad)," absolute=",q.absolute_error," relative=",q.relative_error," cutoff=",c.cutoff)
 for i in first(bad,30)
  js=rows.rowval[nzrange(rows,i)];vs=rows.nzval[nzrange(rows,i)]
  println("ROW ",i," rhs=",c.rhs[i]," residual=",s.residual[i]," scale=",s.work_scale[i]," columns=",js," a=",vs," x=",x[js])
 end
end
quality("COMPONENT before",x,c,s)
println("PROPOSE ",JS._native_phase_homogeneous_component!(x,c.B,rows,c.rhs,c.policy,c.cutoff,s,()->false))
quality("COMPONENT after",x,c,s)
println("CHANGED ",count(!iszero,x-c.x))
