# Keep the original shadow oracle and publication observer. The eligibility
# decision must come from the integrated code, without a process-local override.
const original_worker = pop!(ARGS)
let source = read(original_worker, String)
    archived = occursin("direct-ft-local-check-reuse", original_worker) ?
        "runtime-full-chain-comparison/direct-extension" :
        "runtime-full-chain-comparison/ss-bg-breakdown"
    needle = "diagnostics/" * archived * "/reproduce/direct.jl"
    @assert count(needle, source) == 1
    source = replace(source, needle => "diagnostics/basis-direct-lu/reproduce/direct.jl")
    block = """if arm in ("unit","shadow","candidate")
    # Exactly one eligibility condition changes. All stop/policy/alias checks stay in the shared code.
    install_method("_can_reuse_dual_checks",("ws.factorization isa _NativeDualCheckFactor"=>"Main.eligible(ws.factorization)",))
end
"""
    @assert count(block, source) == 1
    source = replace(source, block => "")
    @assert !occursin("install_method(\"_can_reuse_dual_checks\"", source)
    Base.include_string(Main, source, original_worker)
end
