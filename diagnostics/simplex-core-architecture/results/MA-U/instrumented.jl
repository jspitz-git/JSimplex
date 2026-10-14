# UNEXECUTED diagnostic-only entry clones. NEVER include in timing windows.
const _route_entries = Ref(0)
const _route_scratches = Ref(0)
const _route_fallbacks = Ref(0)
function reset_route_counts!()
    _route_entries[]=0; _route_scratches[]=0; _route_fallbacks[]=0
end
route_counts() = (entries=_route_entries[], scratches=_route_scratches[], fallbacks=_route_fallbacks[])

function instrumented_forward!(dest, backend, rhs)
    _route_entries[] += 1
    if !_dense_ma_eligible(dest, backend, rhs)
        _route_fallbacks[] += 1
        return reference_forward!(dest, backend, rhs)
    end
    _route_scratches[] += 1
    product = BigFloat()
    require_one_based_indexing(dest, rhs)
    _ma_lu_forward!(backend.factorization, copyto!(dest, rhs), product)
    return dest
end
function instrumented_transpose!(dest, backend, rhs)
    _route_entries[] += 1
    if !_dense_ma_eligible(dest, backend, rhs)
        _route_fallbacks[] += 1
        return reference_transpose!(dest, backend, rhs)
    end
    _route_scratches[] += 1
    product = BigFloat()
    require_one_based_indexing(dest, rhs)
    _ma_lu_transpose!(transpose(backend.factorization), copyto!(dest, rhs), product)
    return dest
end

