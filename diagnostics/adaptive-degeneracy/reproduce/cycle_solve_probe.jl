# Separate reconstruction reliability from the point's bound infeasibility.
using JSimplex,Serialization,LinearAlgebra,SparseArrays
BLAS.set_num_threads(1)
ws=deserialize(ARGS[1]);B=JSimplex.basis_matrix(ws);policy=ws.progress.numerical_policy
function quality(B,x,rhs;transposed=false)
    JSimplex._compensated_solve_quality!(JSimplex.SolveQualityScratch(Float64,length(rhs)),B,x,rhs,policy,transposed)
end
rhs=JSimplex._basis_primal_rhs(ws);basic=ws.primal[ws.basis.basic_indices]
for method in (:cleanup,:phase)
    x=copy(basic)
    ok=method==:cleanup ? JSimplex._native_cleanup_solve!(x,ws,B,rhs,()->false) :
        JSimplex._native_phase_primal_solve!(x,ws,B,rhs,()->false)
    println("PRIMAL ",method," accepted=",ok," quality=",quality(B,x,rhs)," change=",maximum(abs,x-basic));flush(stdout)
end
cb=ws.costs[ws.basis.basic_indices];dual=copy(ws.scratch.rho)
x=copy(dual);ok=JSimplex._native_cleanup_solve!(x,ws,B,cb,()->false;transposed=true)
println("DUAL cleanup accepted=",ok," quality=",quality(B,x,cb;transposed=true)," change=",maximum(abs,x-dual))
scratch=JSimplex.SolveQualityScratch(Float64,length(cb));JSimplex._compensated_solve_quality!(scratch,B,dual,cb,policy,true)
correction=similar(dual);JSimplex.transpose_solve!(correction,ws.factorization,scratch.residual)
x=dual+correction;cutoff=policy.solve_tolerance*maximum(abs,correction)
println("DUAL corrected quality=",quality(B,x,cb;transposed=true)," cutoff=",cutoff)
ok=JSimplex._native_phase_local_rows!(x,copy(transpose(B)),cb,policy,cutoff,()->false)
println("DUAL local accepted=",ok," quality=",quality(B,x,cb;transposed=true));flush(stdout)
