using JSimplex,SparseArrays,Test
function check()
 n=2048;p=LinearProblem(spdiagm(0=>ones(n)),zeros(n);row_lower=zeros(n))
 w=JSimplex.initialize_workspace(p,SolverOptions(;algorithm=:primal,verbose=false))
 w.primal .= 1.0;x=ones(n);bounds=(zeros(n),fill(2.0,n))
 @test JSimplex._legacy_primal_row_consistent(w,w.options.primal_tolerance,x,bounds)
 bytes=@allocated JSimplex._legacy_primal_row_consistent(w,w.options.primal_tolerance,x,bounds)
 println("FALLBACK_BYTES=",bytes)
end
check()
