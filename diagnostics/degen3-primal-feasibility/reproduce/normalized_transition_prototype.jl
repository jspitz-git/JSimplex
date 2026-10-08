# Diagnostic-only reuse of the existing native normalization at legacy exit.
using JSimplex
source=read(joinpath(dirname(pathof(JSimplex)),"primal_simplex.jl"),String)
start=findfirst("function _solve_continuous_primal(",source).start
body=source[start:end]
needle="            for artificial in 1:artificial_count\n"
@assert count(needle,body)==1
insertion="""
            if _native_phase_transfer_enabled(workspace)
                mapping=(artificial_columns=(column_count+1):(column_count+artificial_count),)
                if !_normalize_phase_artificial_bounds!(workspace,mapping,original,policy,stop_requested)
                    return _recover_original_failure(original,
                        _internal_solution(workspace,NUMERICAL_ERROR,"legacy artificial normalization failed"),stop_requested)
                end
            end
"""
body=replace(body,needle=>insertion*needle)
Base.include_string(JSimplex,body,"diagnostic-normalized-phase-transition")
include("capture.jl")
write(joinpath(ARGS[1],"override-source.jl"),body)
