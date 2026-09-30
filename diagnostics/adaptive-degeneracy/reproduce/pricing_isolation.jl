# The production adaptive_pricing flag also enables a separate primal
# weak-pivot preference. Disable only that preference in this diagnostic process
# so it cannot confound the pricing lifecycle experiment. All numerical checks
# and the bounded rejection/retry machinery retain their exact source.
function isolate_pricing_trials!()
    source = read(joinpath(dirname(pathof(JSimplex)),"primal_simplex.jl"),String)
    first_index = first(findfirst("function _legacy_primal_iteration!",source))
    last_index = first(findnext("\nfunction ",source,first_index+1))-1
    original = source[first_index:last_index]
    expression = "defer_weak = workspace.progress.numerical_policy.adaptive_pricing"
    @assert count(expression,original) == 1
    isolated = replace(original,expression=>"defer_weak = false")
    Base.include_string(JSimplex,isolated,"diagnostic_pricing_only.jl")
    return bytes2hex(sha256(isolated))
end
