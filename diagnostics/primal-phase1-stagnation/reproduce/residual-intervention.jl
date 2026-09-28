# Diagnostic override for historical checkouts. The original experiment
# exposed a separate point-reconstruction failure; later source may already
# use this gate with the certified point-preservation repair.
function install_residual_intervention(; trace=false)
    source=read(joinpath(dirname(pathof(JSimplex)),"legacy_primal_pivot.jl"),String)
    first=findfirst("function _legacy_primal_direction_pivot_ok!",source)
    isnothing(first) && error("Pivot probe method not found")
    method=source[first.start:end]
    old="(isnothing(quality) || !quality.finite || !quality.reliable) && return false"
    native="(isnothing(quality) || !quality.finite) && return false"
    if count(old,method)==1
        method=replace(method,old=>native;count=1)
    else
        count(native,method)==1 || error("Residual intervention anchor changed")
    end
    if trace
        old="return abs(buffers.correction[leaving_row]) <= relative * abs(pivot)"
        count(old,method)==1 || error("Residual trace anchor changed")
        method=replace(method,old=>"""
        accepted=abs(buffers.correction[leaving_row]) <= relative * abs(pivot)
        if accepted && !quality.reliable
            println("NEW_ACCEPT iter=",workspace.iterations," entering=",entering,
                " row=",leaving_row," pivot=",pivot," norm=",maximum(abs,column),
                " quality=",quality," correction_norm=",maximum(abs,buffers.correction),
                " pivot_correction=",buffers.correction[leaving_row]);flush(stdout)
        end
        return accepted
        """;count=1)
    end
    Base.include_string(JSimplex,method,"diagnostic-finite-residual-probe.jl")
end
