module _InequalityProofs

using SparseArrays

const JS = parentmodule(@__MODULE__)
const Q = Rational{BigInt}
const Endpoint = Union{Nothing,Q}

struct DirectionCertificate
    row::Int
    side::Symbol
    columns::Vector{Int}
    values::Vector{Q}
end

struct SingletonBoxCertificate
    row::Int
    side::Symbol
    column::Int
end

const Certificate = Union{DirectionCertificate,SingletonBoxCertificate}

struct Node
    column::Int
    move::Q
    parents::Vector{Tuple{Int,Q}}
end

struct Term
    row::Int
    coefficient::Q
    contribution::Endpoint
    node::Int
end

inc!(stats, key, count=1) = (stats[key] = get(stats, key, 0) + count)
q(x) = JS._exact_rational(x)
reject(message) = throw(ArgumentError(message))
column_entries(A, j) = nzrange(A, j)
is_singleton(A, j) = length(column_entries(A, j)) == 1

function target_bound(p, cert)
    1 <= cert.row <= size(p.A, 1) && cert.side in (:lower, :upper) || reject("invalid target")
    target = cert.side == :lower ? p.row_lower[cert.row] : p.row_upper[cert.row]
    isfinite(target) || reject("infinite target")
    return target
end

function check(p, cert::DirectionCertificate, rows)
    target_bound(p, cert)
    r = cert.row
    cols, values = cert.columns, cert.values
    length(cols) == length(values) == length(unique(cols)) || reject("invalid direction dimensions")
    acts = Dict{Int,Q}()
    cost = zero(Q)
    for (j, v) in zip(cols, values)
        1 <= j <= size(p.A, 2) || reject("invalid column")
        ((v < 0 && isfinite(p.column_lower[j])) ||
         (v > 0 && isfinite(p.column_upper[j]))) && reject("column blocks direction")
        cost += q(p.objective[j]) * v
        for k in column_entries(p.A, j)
            i = p.A.rowval[k]
            acts[i] = get(acts, i, zero(Q)) + q(p.A.nzval[k]) * v
        end
    end
    p.objective_sense == JS.MAX_SENSE && (cost = -cost)
    cost <= 0 || reject("objective worsens")
    v = get(acts, r, zero(Q))
    (cert.side == :lower ? v < 0 : v > 0) || reject("target does not approach bound")
    for (i, activity) in acts
        i == r && continue
        ((activity < 0 && isfinite(p.row_lower[i])) ||
         (activity > 0 && isfinite(p.row_upper[i]))) && reject("other row blocks direction")
    end
    return acts
end

function check(p, cert::SingletonBoxCertificate, rows)
    target = target_bound(p, cert)
    r, j = cert.row, cert.column
    1 <= j <= size(p.A, 2) || reject("invalid column")
    length(rows[r]) >= 2 || reject("singleton row excluded")
    entries = column_entries(p.A, j)
    length(entries) == 1 && p.A.rowval[first(entries)] == r ||
        reject("not a singleton column of the target row")
    a = q(p.A.nzval[first(entries)])
    iszero(a) && reject("zero pivot")
    ratio = q(p.objective[j]) / a
    p.objective_sense == JS.MAX_SENSE && (ratio = -ratio)
    (cert.side == :lower ? ratio >= 0 : ratio <= 0) || reject("singleton objective sign")
    min_activity = max_activity = zero(Q)
    for (other, stored) in rows[r]
        other == j && continue
        b = q(stored)
        lower = b > 0 ? p.column_lower[other] : p.column_upper[other]
        upper = b > 0 ? p.column_upper[other] : p.column_lower[other]
        min_activity = isnothing(min_activity) || !isfinite(lower) ?
            nothing : min_activity + b * q(JS.bound_value(lower))
        max_activity = isnothing(max_activity) || !isfinite(upper) ?
            nothing : max_activity + b * q(JS.bound_value(upper))
    end
    rhs = q(JS.bound_value(target))
    lo = isnothing(max_activity) ? nothing : (rhs - max_activity) / a
    up = isnothing(min_activity) ? nothing : (rhs - min_activity) / a
    a < 0 && ((lo, up) = (up, lo))
    isfinite(p.column_lower[j]) &&
        (isnothing(lo) || lo < q(JS.bound_value(p.column_lower[j]))) &&
        reject("singleton lower obstruction")
    isfinite(p.column_upper[j]) &&
        (isnothing(up) || up > q(JS.bound_value(p.column_upper[j]))) &&
        reject("singleton upper obstruction")
    return Dict(r => Q(cert.side == :lower ? -1 : 1))
end

function activate(p::JS.LinearProblem{T}, certs) where T
    all(==(JS.CONTINUOUS), p.variable_domains) || reject("LP only")
    isempty(certs) && return p
    rows = any(c -> c isa SingletonBoxCertificate, certs) ? JS._row_entries(p.A) : nothing
    targets = Set{Int}()
    touched = Set{Int}()
    for c in certs
        r = c.row
        r in targets && reject("duplicate activation")
        acts = check(p, c, rows)
        (r in touched || any(i != r && !iszero(v) && i in targets for (i, v) in acts)) &&
            reject("incompatible activation batch")
        push!(targets, r)
        for (i, v) in acts
            i != r && !iszero(v) && push!(touched, i)
        end
    end

    lo, up = copy(p.row_lower), copy(p.row_upper)
    for c in certs
        r = c.row
        lo[r] = up[r] = c.side == :lower ? lo[r] : up[r]
    end
    return JS._presolve_model(Val(48),p.A, p.objective, p.objective_constant, p.objective_sense,
        lo, up, p.column_lower, p.column_upper, p.variable_domains, p.name,
        p.row_names, p.column_names)
end

function heappush!(heap, value)
    push!(heap, value)
    i = length(heap)
    while i > 1
        parent = i >> 1
        heap[parent] >= value && break
        heap[i] = heap[parent]
        i = parent
    end
    heap[i] = value
end

function heappop!(heap)
    top = heap[1]
    value = pop!(heap)
    isempty(heap) && return top
    i = 1
    while 2i <= length(heap)
        child = 2i
        child < length(heap) && heap[child + 1] > heap[child] && (child += 1)
        heap[child] <= value && break
        heap[i] = heap[child]
        i = child
    end
    heap[i] = value
    return top
end

function expand(nodes, root, budget)
    weights = Dict(root => one(Q))
    heap = [root]
    direction = Dict{Int,Q}()
    visited = edges = 0
    # Descending node IDs accumulate every descendant's contribution before visiting a node.
    while !isempty(heap)
        k = heappop!(heap)
        weight = pop!(weights, k)
        visited += 1
        visited > budget && return nothing, visited, edges
        node = nodes[k]
        edges + length(node.parents) > budget && return nothing, visited, edges
        edges += length(node.parents)
        if node.column != 0
            direction[node.column] = get(direction, node.column, zero(Q)) + weight * node.move
        end
        for (parent, factor) in node.parents
            @assert parent < k
            if !haskey(weights, parent)
                heappush!(heap, parent)
                weights[parent] = zero(Q)
            end
            weights[parent] += weight * factor
        end
    end
    filter!(entry -> !iszero(entry.second), direction)
    return direction, visited, edges
end

function infer(p; work_limit=1_000_000, rounds=8, expand_limit=5000,
               stop_requested=() -> false)
    m, n = size(p.A)
    stats = Dict{String,Int}()
    # A stopped search discards every candidate, including already checked ones.
    (m == 0 || n == 0 || nnz(p.A) == 0 || stop_requested()) && return Certificate[], stats
    nodes = Node[]
    empty_parents = Tuple{Int,Q}[]
    lo = fill!(Vector{Endpoint}(undef, m), nothing)
    up = copy(lo)
    ln, un = zeros(Int, m), zeros(Int, m)
    for i in 1:m
        stop_requested() && return Certificate[], stats
        if !isfinite(p.row_upper[i])
            push!(nodes, Node(0, zero(Q), empty_parents))
            lo[i] = zero(Q)
            ln[i] = length(nodes)
        end
        if !isfinite(p.row_lower[i])
            push!(nodes, Node(0, zero(Q), empty_parents))
            up[i] = zero(Q)
            un[i] = length(nodes)
        end
    end
    initial = length(nodes)
    exhausted = inconsistent = false
    terms = Term[]
    stop_requested() && return Certificate[], stats
    aq = fill!(Vector{Endpoint}(undef, nnz(p.A)), nothing)
    cost = fill!(Vector{Endpoint}(undef, n), nothing)
    coefficient(k) = isnothing(aq[k]) ? (aq[k] = q(p.A.nzval[k]))::Q : aq[k]::Q
    sense = p.objective_sense == JS.MIN_SENSE ? 1 : -1
    costvalue(j) = isnothing(cost[j]) ? (cost[j] = q(p.objective[j]) * sense)::Q : cost[j]::Q
    for turn in 1:rounds
        changed = false
        stats["rounds"] = turn
        for j in 1:n
            stop_requested() && return Certificate[], stats
            entries = column_entries(p.A, j)
            isempty(entries) && continue
            for sign in (1, -1)
                isfinite(sign == 1 ? p.column_lower[j] : p.column_upper[j]) && continue
                if get(stats, "term_visits", 0) + length(entries) > work_limit
                    exhausted = true
                    break
                end
                inc!(stats, "term_visits", length(entries))
                empty!(terms)
                total = zero(Q)
                missing = 0
                for k in entries
                    i = p.A.rowval[k]
                    a = sign * coefficient(k)
                    if iszero(a)
                        stats["stored_zero_declined"] = 1
                        return Certificate[], stats
                    end
                    v, id = a > 0 ? (up[i], un[i]) : (lo[i], ln[i])
                    contribution = isnothing(v) ? nothing : a * v
                    missing += isnothing(contribution)
                    !isnothing(contribution) && (total += contribution)
                    push!(terms, Term(i, a, contribution, id))
                end
                for t in terms
                    missing - Int(isnothing(t.contribution)) != 0 && continue
                    beta = (sign * costvalue(j) - (total - something(t.contribution, zero(Q)))) /
                        abs(t.coefficient)
                    lower = t.coefficient > 0
                    value = lower ? beta : -beta
                    bounds, ids = lower ? (lo, ln) : (up, un)
                    old, oldid = bounds[t.row], ids[t.row]
                    improves = isnothing(old) || (lower ? value > old : value < old)
                    equalbase = !isnothing(old) && old == value && 0 < oldid <= initial
                    (improves || equalbase) || continue
                    if get(stats, "proof_edges", 0) + length(terms) - 1 > work_limit
                        exhausted = true
                        break
                    end
                    parents = Tuple{Int,Q}[(u.node, abs(u.coefficient) / abs(t.coefficient))
                        for u in terms if u.row != t.row]
                    @assert all(parent -> parent[1] != 0, parents)
                    inc!(stats, "proof_edges", length(parents))
                    push!(nodes, Node(j, Q(-sign) / abs(t.coefficient), parents))
                    bounds[t.row] = value
                    ids[t.row] = length(nodes)
                    changed = true
                    inc!(stats, "bound_updates")
                    if !isnothing(lo[t.row]) && !isnothing(up[t.row]) && lo[t.row] > up[t.row]
                        inconsistent = true
                        break
                    end
                end
                inconsistent && break
            end
            (exhausted || inconsistent) && break
        end
        (exhausted || inconsistent || !changed) && break
    end
    stats["nodes"] = length(nodes)
    stats["work_exhausted"] = Int(exhausted)
    stats["inconsistent_dual_intervals"] = Int(inconsistent)

    candidates = Tuple{Certificate,Vector{Int}}[]
    if !inconsistent
        for i in 1:m
            stop_requested() && return Certificate[], stats
            isfinite(p.row_lower[i]) && p.row_lower[i] == p.row_upper[i] && continue
            for (side, value, root) in ((:lower, lo[i], ln[i]), (:upper, up[i], un[i]))
                bound = side == :lower ? p.row_lower[i] : p.row_upper[i]
                (!isfinite(bound) || root <= initial) && continue
                (side == :lower ? value < 0 : value > 0) && continue
                stop_requested() && return Certificate[], stats
                budget = min(expand_limit, max(0, work_limit - get(stats, "expansion_edges", 0)))
                d, visited, edges = expand(nodes, root, budget)
                inc!(stats, "proof_nodes_visited", visited)
                inc!(stats, "expansion_edges", edges)
                if isnothing(d)
                    inc!(stats, "proof_budget_rejections")
                    continue
                end
                stop_requested() && return Certificate[], stats
                cols = sort!(collect(keys(d)))
                cert = DirectionCertificate(i, side, cols, [d[j] for j in cols])
                acts = try
                    check(p, cert, nothing)
                catch e
                    e isa ArgumentError || rethrow()
                    inc!(stats, "direction_rejections")
                    continue
                end
                factor = inv(abs(acts[i]))
                cert.values .*= factor
                affected_rows = Int[r for (r, a) in acts if r != i && !iszero(a)]
                push!(candidates, (cert, affected_rows))
            end
        end
    end

    has_singleton = false
    for j in 1:n
        stop_requested() && return Certificate[], stats
        if is_singleton(p.A, j)
            has_singleton = true
            break
        end
    end
    if has_singleton
        rows = JS._PresolveWork.rows(p.A)
        stop_requested() && return Certificate[], stats
        cl = fill!(Vector{Endpoint}(undef, n), nothing)
        cu = copy(cl)
        function cb(j, upper)
            source, cache = upper ? (p.column_upper, cu) : (p.column_lower, cl)
            !isfinite(source[j]) && return nothing
            isnothing(cache[j]) && (cache[j] = q(JS.bound_value(source[j])))
            return cache[j]::Q
        end
        unaffected = Int[]
        for i in 1:m
            stop_requested() && return Certificate[], stats
            isfinite(p.row_lower[i]) && p.row_lower[i] == p.row_upper[i] && continue
            entries = rows[i]
            any(entry -> is_singleton(p.A, entry[1]), entries) || continue
            if get(stats, "singleton_term_visits", 0) + length(entries) > work_limit
                stats["singleton_work_exhausted"] = 1
                break
            end
            inc!(stats, "singleton_term_visits", length(entries))
            smn = smx = zero(Q)
            imn = imx = 0
            for (j, a0) in entries
                a = q(a0)
                low, high = cb(j, a <= 0), cb(j, a > 0)
                isnothing(low) ? (imn += 1) : (smn += a * low)
                isnothing(high) ? (imx += 1) : (smx += a * high)
            end
            for (j, a0) in entries
                is_singleton(p.A, j) || continue
                stop_requested() && return Certificate[], stats
                inc!(stats, "singleton_trials")
                length(entries) >= 2 || continue
                a = q(a0)
                if iszero(a)
                    stats["stored_zero_declined"] = 1
                    return Certificate[], stats
                end
                ratio = costvalue(j) / a
                lower_bound, upper_bound = cb(j, false), cb(j, true)
                low, high = a > 0 ? (lower_bound, upper_bound) : (upper_bound, lower_bound)
                for side in (:lower, :upper)
                    target = side == :lower ? p.row_lower[i] : p.row_upper[i]
                    isfinite(target) || continue
                    (side == :lower ? ratio < 0 : ratio > 0) && continue
                    mn = imn - Int(isnothing(low)) != 0 ? nothing : smn - (isnothing(low) ? zero(Q) : a * low)
                    mx = imx - Int(isnothing(high)) != 0 ? nothing : smx - (isnothing(high) ? zero(Q) : a * high)
                    rhs = q(JS.bound_value(target))
                    lower = isnothing(mx) ? nothing : (rhs - mx) / a
                    upper = isnothing(mn) ? nothing : (rhs - mn) / a
                    a < 0 && ((lower, upper) = (upper, lower))
                    !isnothing(lower_bound) && (isnothing(lower) || lower < lower_bound) && continue
                    !isnothing(upper_bound) && (isnothing(upper) || upper > upper_bound) && continue
                    push!(candidates, (SingletonBoxCertificate(i, side, j), unaffected))
                    break
                end
            end
        end
    end

    selected = Certificate[]
    chosen = Set{Int}()
    touched = Set{Int}()
    for (cert, affected_rows) in candidates
        stop_requested() && return Certificate[], stats
        i = cert.row
        if i in chosen
            inc!(stats, "duplicate_rows")
            continue
        end
        if i in touched || any(in(chosen), affected_rows)
            inc!(stats, "batch_conflicts")
            continue
        end
        push!(chosen, i)
        union!(touched, affected_rows)
        push!(selected, cert)
    end
    stop_requested() && return Certificate[], stats
    stats["candidate_certificates"] = length(candidates)
    stats["selected_rows"] = length(selected)
    stats["selected_direction"] = count(c -> c isa DirectionCertificate, selected)
    stats["selected_singleton_box"] = length(selected) - stats["selected_direction"]
    return selected, stats
end

end
