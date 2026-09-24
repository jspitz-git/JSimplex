module JSimplexPipelineComponents
using JSimplex,SparseArrays,LinearAlgebra

"""Exercise a bounded synthetic pipeline; never factor an original full model."""
function probe(B::SparseMatrixCSC{Float64,Int};stop=()->false)
    n,m = size(B)
    n == m || throw(DimensionMismatch("Pipeline component must be square"))
    n <= 32 || throw(ArgumentError("Pipeline component exceeds 32x32"))
    all(isfinite,nonzeros(B)) || throw(ArgumentError("Pipeline component must be finite"))
    methods = Dict{String,Any}[]
    result = Dict{String,Any}("basis_dimension"=>n,"basis_nonzeros"=>nnz(B),
        "simplex_solve"=>false,"full_sized_factorization"=>false,
        "interrupted"=>false,"methods"=>methods)
    for method in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub),backend in (:native,:markowitz)
        stop() && (result["interrupted"]=true;return result)
        diagnostics = JSimplex.SimplexDiagnostics(kernel_timing=true)
        p = LinearProblem(B,zeros(n))
        policy = JSimplex.NumericalPolicy(Float64;hypersparse=true)
        options = SolverOptions(verbose=false,basis_update=method,basis_refactorization=backend)
        setup = @timed begin
            ws = JSimplex.initialize_workspace(p,options;
                progress=JSimplex.SimplexProgressContext(p;diagnostics,numerical_policy=policy))
            ws.basis = JSimplex.Basis(collect(1:n),vcat(fill(JSimplex.BASIC,n),fill(JSimplex.FREE_NONBASIC,n)))
            JSimplex.recompute!(ws;refactorize=true)
            ws
        end
        ws = setup.value
        profiles = Dict{String,Any}[]
        report = Dict{String,Any}("basis_update"=>string(method),"backend"=>string(backend),
            "setup_seconds"=>setup.time,"setup_allocated_bytes"=>setup.bytes,
            "profiles"=>profiles,"reference_verified"=>true)
        push!(methods,report)
        reference = setprecision(()->lu(Matrix{BigFloat}(B)),BigFloat,256)
        # Alternating full and unit RHS exercises clearing and dense-to-sparse
        # transitions; both forced modes remain independently available.
        for (kind,mode) in ((:unit,:sparse),(:full,:dense),(:unit,:auto),(:empty,:auto)),
            transposed in (false,true)
            stop() && (result["interrupted"]=true;return result)
            buffer = JSimplex._pipeline_rhs_buffer!(ws)
            if kind == :unit && n > 0
                JSimplex._set_pipeline_rhs!(buffer,1,1.0)
            elseif kind == :full
                for i in 1:n
                    JSimplex._set_pipeline_rhs!(buffer,i,isodd(i) ? 1.0 : -1.0)
                end
            end
            rhs = JSimplex._pipeline_rhs_values(buffer)
            expected = setprecision(BigFloat,256) do
                transposed ? transpose(reference)\BigFloat.(rhs) : reference\BigFloat.(rhs)
            end
            measured = @timed begin
                JSimplex._pipeline_basis_solve!(ws.scratch.rho,ws,rhs;
                    transposed,kernel_mode=mode)
                JSimplex._pipeline_price!(ws.scratch.tableau_row,ws,ws.scratch.rho;kernel_mode=mode)
            end
            expected_price = setprecision(()->vcat(transpose(B)*expected,-expected),BigFloat,256)
            for (actual,wanted) in ((ws.scratch.rho,expected),(ws.scratch.tableau_row,expected_price))
                error = maximum(abs,BigFloat.(actual)-wanted;init=BigFloat(0))
                error <= 1024eps(Float64)*max(BigFloat(1),maximum(abs,wanted;init=BigFloat(0))) ||
                    Base.error("Pipeline component disagrees with the independent reference")
                Set(JSimplex._pipeline_vector!(ws,actual).indices) == Set(findall(!iszero,actual)) ||
                    Base.error("Pipeline component retained stale support")
            end
            push!(profiles,Dict("rhs_kind"=>string(kind),"mode"=>string(mode),
                "transposed"=>transposed,"seconds"=>measured.time,"allocated_bytes"=>measured.bytes,
                "rhs_support"=>count(!iszero,rhs),"solution_support"=>count(!iszero,ws.scratch.rho),
                "price_support"=>count(!iszero,ws.scratch.tableau_row),"reference_verified"=>true))
        end
        report["factor_storage_entries"] = JSimplex._factor_storage_count(ws.factorization)
        report["factor_cache_bytes"] = Base.summarysize(ws.factorization.sparse)
        # This reachable size includes borrowed model/scratch arrays. It must
        # not be summed with workspace or shared candidate storage.
        report["pipeline_reachable_bytes"] = Base.summarysize(ws.scratch.hypersparse)
        report["support_rebuilds"] = ws.scratch.hypersparse.support_rebuilds
        report["kernel_calls"] = Dict(string(k)=>v for (k,v) in diagnostics.kernel_calls)
        report["kernel_seconds"] = Dict(string(k)=>Float64(v)/1e9 for (k,v) in diagnostics.kernel_nanoseconds)
    end
    return result
end
end
