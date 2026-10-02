# Diagnose the next artificial-removal boundary without changing production.
using JSimplex,Serialization,LinearAlgebra
BLAS.set_num_threads(1)
function scan_candidates(ws,map,row,rho,B)
    policy=ws.progress.numerical_policy
    m=length(rho);rhs=zeros(m);column=zeros(m)
    prices=zeros(length(ws.basis.states));JSimplex._csc_price!(prices,ws.problem.A,rho)
    counts=Dict{Symbol,Int}();eligible=0;bad_column=0
    for j in map.original_to_phase
        ws.basis.states[j]==JSimplex.BASIC && continue
        iszero(prices[j]) && continue
        JSimplex._pivot_column!(rhs,ws,j)
        JSimplex._checked_basis_solve!(column,ws,rhs,()->false)
        abs(column[row])>policy.pivot_error_tolerance*maximum(abs,column;init=0.0) || continue
        eligible+=1
        quality=JSimplex.solve_quality!(JSimplex.SolveQualityScratch(Float64,m),B,column,rhs,policy)
        bad_column+=!quality.reliable
        result=JSimplex.validate_pivot!(ws,JSimplex.PivotCandidate(j,row,prices[j],column,rho),policy)
        counts[result]=get(counts,result,0)+1
    end
    println("SCAN eligible=",eligible," bad_columns=",bad_column," decisions=",counts);flush(stdout)
end
function main(prefix)
    ws=deserialize(prefix*"-phase.bin");map=deserialize(prefix*"-map.bin")
    B=JSimplex.basis_matrix(ws);m=size(B,1);policy=ws.progress.numerical_policy
    row=findfirst(j->iszero(map.phase_to_original[j]),ws.basis.basic_indices)
    @assert !isnothing(row)
    unit=zeros(m);unit[row]=1.0;rho=zeros(m)
    JSimplex._checked_basis_solve!(rho,ws,unit,()->false;transposed=true)
    quality(x)=JSimplex.solve_quality!(JSimplex.SolveQualityScratch(Float64,m),B,x,unit,policy;transposed=true)
    println("ARTIFICIAL row=",row," column=",ws.basis.basic_indices[row]," value=",ws.primal[ws.basis.basic_indices[row]])
    println("ROW_BEFORE ",quality(rho));flush(stdout)
    scan_candidates(ws,map,row,rho,B)
    trial=copy(rho)
    println("NATIVE_ROW_CORRECTION ",JSimplex._native_cleanup_solve!(trial,ws,B,unit,()->false;transposed=true))
    println("ROW_AFTER ",quality(trial));flush(stdout)
    scan_candidates(ws,map,row,trial,B)
end
main(ARGS[1])
