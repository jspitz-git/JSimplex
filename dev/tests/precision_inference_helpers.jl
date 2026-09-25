# Cold recovery and nested correction solves deliberately isolate inference.
# Only dispatch at these exact methods is allowed; all direct kernels remain strict.
function is_precision_entry_dispatch(report)
    report isa JET.RuntimeDispatchReport || return false
    isempty(report.vst) && return false
    method = last(report.vst).linfo.def
    return any(f -> method === only(methods(f)),
        (JSimplex._dispatch_precision_recovery, JSimplex._dispatch_numerical_recovery,
         JSimplex._dispatch_lp_auxiliary))
end

unexpected_precision_reports(report) =
    filter(r -> !is_precision_entry_dispatch(r), JET.get_reports(report))
