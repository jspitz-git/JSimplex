include("restore.jl")
w=restore_bg(ARGS[1]);B=JS.basis_matrix(w);rhs=w.costs[w.basis.basic_indices];x=copy(w.scratch.rho);p=w.progress.numerical_policy;s=JS.SolveQualityScratch(Float64,length(rhs));JS._compensated_solve_quality!(s,B,x,rhs,p,true);d=similar(x);JS.transpose_solve!(d,w.factorization,s.residual);y=x+d
for j in (27613,)
 println("ROW ",j," rhs=",rhs[j])
 for q in nzrange(B,j)
  i=B.rowval[q]
  println((i,B.nzval[q],x[i],d[i],y[i]))
 end
end
