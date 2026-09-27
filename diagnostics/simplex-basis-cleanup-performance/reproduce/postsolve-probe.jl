# Solve JSimplex's reduced LP independently, then exercise its original postsolve.
# Requires the locally installed HiGHS C library; never changes solver defaults.
using JSimplex, SparseArrays, LinearAlgebra, Serialization
const HIGHS = get(ENV,"HIGHS_LIBRARY","/home/jspitz/.julia/artifacts/664e3659d6b26b70e764cb87b2ba2e87a33e2053/lib/libhighs.so.1.15.0")
check(code) = code in (0, 1) || error("HiGHS call failed: $code")
bound_number(b,lower) = isfinite(b) ? JSimplex.bound_value(b) : (lower ? -Inf : Inf)
function independent_basis(p)
    m,n=size(p.A)
    h=ccall((:Highs_create,HIGHS),Ptr{Cvoid},())
    try
        check(ccall((:Highs_setIntOptionValue,HIGHS),Cint,(Ptr{Cvoid},Cstring,Cint),h,"threads",1))
        check(ccall((:Highs_setStringOptionValue,HIGHS),Cint,(Ptr{Cvoid},Cstring,Cstring),h,"solver","simplex"))
        check(ccall((:Highs_setDoubleOptionValue,HIGHS),Cint,(Ptr{Cvoid},Cstring,Cdouble),h,"time_limit",360.0))
        check(ccall((:Highs_passLp,HIGHS),Cint,
            (Ptr{Cvoid},Cint,Cint,Cint,Cint,Cint,Cdouble,Ptr{Cdouble},Ptr{Cdouble},Ptr{Cdouble},Ptr{Cdouble},Ptr{Cdouble},Ptr{Cint},Ptr{Cint},Ptr{Cdouble}),
            h,n,m,nnz(p.A),1,1,p.objective_constant,p.objective,
            bound_number.(p.column_lower,true),bound_number.(p.column_upper,false),
            bound_number.(p.row_lower,true),bound_number.(p.row_upper,false),
            Cint.(p.A.colptr.-1),Cint.(p.A.rowval.-1),p.A.nzval))
        check(ccall((:Highs_run,HIGHS),Cint,(Ptr{Cvoid},),h))
        status=ccall((:Highs_getModelStatus,HIGHS),Cint,(Ptr{Cvoid},),h)
        status==7 || error("Reduced reference status $status")
        x=zeros(n); y=zeros(n); a=zeros(m); d=zeros(m)
        check(ccall((:Highs_getSolution,HIGHS),Cint,(Ptr{Cvoid},Ptr{Cdouble},Ptr{Cdouble},Ptr{Cdouble},Ptr{Cdouble}),h,x,y,a,d))
        cs=zeros(Cint,n); rs=zeros(Cint,m)
        check(ccall((:Highs_getBasis,HIGHS),Cint,(Ptr{Cvoid},Ptr{Cint},Ptr{Cint}),h,cs,rs))
        states=map(vcat(cs,rs)) do s
            s==0 ? JSimplex.AT_LOWER : s==1 ? JSimplex.BASIC : s==2 ? JSimplex.AT_UPPER : JSimplex.FREE_NONBASIC
        end
        basis=JSimplex.Basis(findall(==(JSimplex.BASIC),states),states)
        @assert length(basis.basic_indices)==m
        return x,basis
    finally
        ccall((:Highs_destroy,HIGHS),Cvoid,(Ptr{Cvoid},),h)
    end
end
function main()
    path,output=ARGS[1:2]
    lowercase(basename(realpath(path))) in ("big.mps","largo.mps","anymod.mps") && error("Excluded large model")
    problem=JSimplex.relax_integrality(read_mps(path))
    println("Presolving ",path);flush(stdout)
    reduced=JSimplex.presolve_problem(problem)
    println("Reduced dimensions ",size(reduced.problem.A));flush(stdout)
    x,basis=independent_basis(reduced.problem)
    target=JSimplex.postsolve_primal(reduced,x)
    restored=JSimplex.restore_basis(reduced,basis)
    serialize(output,(problem=problem,target=target,basis=restored))
    println("Saved reconstruction input ",output," target_feasible=",JSimplex._original_primal_feasible(problem,target,1e-7));flush(stdout)
    options=SolverOptions(basis_update=:bartels_golub,algorithm=:dual,pricing=:steepest_edge,refactorization_interval=80)
    ws=JSimplex.initialize_workspace(problem,options)
    ws.basis=restored
    JSimplex.recompute!(ws;refactorize=true)
    println("Restored pinf=",JSimplex.primal_infeasibility(ws)," dinf=",JSimplex.dual_infeasibility(ws));flush(stdout)
    elapsed=@elapsed exchanges=JSimplex._project_postsolve_basis!(ws,target,()->false)
    projected=ws.primal[1:length(target)]
    println("Projection exchanges=",exchanges," seconds=",elapsed,
        " pinf=",JSimplex.primal_infeasibility(ws)," dinf=",JSimplex.dual_infeasibility(ws),
        " max_target_difference=",maximum(abs.(projected-target)),
        " original_feasible=",JSimplex._original_primal_feasible(problem,projected,options.primal_tolerance),
        " objective=",dot(problem.objective,projected)+problem.objective_constant)
end
main()
