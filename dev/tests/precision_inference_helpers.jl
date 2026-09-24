# Automatic escalation deliberately crosses one cold inference boundary so an
# ordinary solve does not infer every higher-precision simplex kernel. Reject
# every other dispatch report; direct precision-kernel checks remain strict.
function is_precision_entry_dispatch(report)
    report isa JET.RuntimeDispatchReport || return false
    isempty(report.vst) && return false
    return last(report.vst).linfo.def === only(methods(JSimplex._dispatch_precision_recovery))
end

unexpected_precision_reports(report) =
    filter(r -> !is_precision_entry_dispatch(r), JET.get_reports(report))
