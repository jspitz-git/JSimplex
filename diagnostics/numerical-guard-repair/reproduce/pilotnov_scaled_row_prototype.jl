# Isolated recovery experiment; no production dispatch is changed on disk.
using JSimplex
source = read(joinpath(dirname(pathof(JSimplex)),"legacy_dual_correction.jl"),String)
body = first(split(source,"# Retain the low BTRAN correction"))
body = replace(body,"_try_native_dual_correction!"=>"_unscaled_native_dual_correction!")
Base.include_string(JSimplex,body,"unscaled-native-correction")
@eval JSimplex begin
    function _try_native_dual_correction!(ws::SimplexWorkspace{T},destination::Vector{T},
            index::Int,row::Int,stop;transposed::Bool=false) where T
        _unscaled_native_dual_correction!(ws,destination,index,row,stop;transposed) && return true
        T===Float64 && transposed && isempty(ws.factorization.updates) && !stop() || return false
        policy=ws.progress.numerical_policy
        (policy.pivot_validation || policy.solve_refinement || policy.recovery) && return false
        B=_basis_matrix!(ws)
        rows=vec(maximum(abs,B;dims=2));rows[iszero.(rows)].=1
        R=spdiagm(1 ./ rows);M=R*B
        cols=vec(maximum(abs,M;dims=1));cols[iszero.(cols)].=1
        C=spdiagm(1 ./ cols)
        f=_factorize_basis(M*C,Val(:markowitz))
        solve=b->R*_refinement_basis_solve(f,C*b,true)
        rhs=zeros(T,size(B,1));rhs[index]=1
        x=solve(rhs);scratch=SolveQualityScratch(T,length(rhs))
        for k in 0:policy.max_refinements
            stop() && return false
            if _dual_row_residual_ratio(ws,x,row)<=1
                copyto!(destination,x);_pipeline_changed!(ws,destination)
                println("SCALED_ROW iteration=",ws.iterations," corrections=",k);flush(stdout)
                return true
            end
            k==policy.max_refinements && break
            q=_compensated_solve_quality!(scratch,B,x,rhs,policy,true)
            (isnothing(q) || !q.finite) && return false
            x .+= solve(scratch.residual)
        end
        return false
    end
end
include("capture.jl")
