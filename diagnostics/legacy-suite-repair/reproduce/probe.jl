using JSimplex,Test,SparseArrays,LinearAlgebra,TOML
const JS=JSimplex
root=dirname(dirname(pathof(JS)))
# Load only fixture definitions, without their already-reproduced assertions.
for file in ("primal_bound_snap_tests.jl","primal_candidate_retry_tests.jl")
 for ex in Meta.parseall(read(joinpath(root,"test",file),String)).args
  ex isa Expr && ex.head == :function && Core.eval(Main,ex)
 end
end
records=[]
for fixed in (false,true), count in (0,1,2,9)
 ws=count==0 ? structural_bound_snap_workspace(0.01;fixed_leaving=false) : unsafe_structural_candidates(count;safe=count!=2,fixed_leaving=false)
 if fixed
  ws.upper[1]=Bound(0.0);ws.problem.column_upper[1]=Bound(0.0)
 end
 before=copy(ws.primal);basis=copy(ws.basis.basic_indices)
 result=JS._primal_iteration!(ws,()->false,ws.options.dual_tolerance)
 rows,cols=size(ws.problem.A)
 push!(records,Dict("kind"=>"structural","fixed"=>fixed,"count"=>count,"status"=>isnothing(result) ? "CONTINUE" : string(result.status),"basis_before"=>basis,"basis_after"=>copy(ws.basis.basic_indices),"primal_before"=>before,"primal_after"=>copy(ws.primal),"original_feasible"=>JS._original_primal_feasible(ws.problem,ws.primal[1:cols],ws.options.primal_tolerance),"row_residual"=>maximum(abs,ws.problem.A*ws.primal[1:cols]-ws.primal[cols+1:end]),"iterations"=>ws.iterations))
end
for columns in (16,256)
 A=spzeros(2,columns);A[2,:].=1.0
 problem=LinearProblem(A,-collect(Float64,columns:-1:1);row_upper=[0.0,1.0])
 options=SolverOptions(algorithm=:primal,simplex_strategy=:legacy,basis_update=:bartels_golub,pricing=:steepest_edge,refactorization_interval=80,verbose=false)
 d=JS.SimplexDiagnostics(;kernel_timing=true)
 ws=JS.initialize_workspace(problem,options;progress=JS.SimplexProgressContext(problem;diagnostics=d))
 ws.factorization.base=JS._factorize_basis(sparse([-1.0 1.0;0.0 -1.0]));JS.replace_column!(ws.factorization,[1.0,0.0],1)
 before=d.kernel_calls[:ftran]
 result=JS._primal_iteration!(ws,()->false,options.dual_tolerance)
 push!(records,Dict("kind"=>"pricing","columns"=>columns,"calls"=>d.kernel_calls[:ftran]-before,"events"=>Dict(string(k)=>v for (k,v) in d.counts),"original_feasible"=>JS._original_primal_feasible(problem,ws.primal[1:columns],options.primal_tolerance)))
end
TOML.print(stdout,Dict("cases"=>records))
