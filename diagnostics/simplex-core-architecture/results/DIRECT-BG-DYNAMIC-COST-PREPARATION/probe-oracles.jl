# UNEXECUTED Task1 tests. Include inside the candidate module only in a future
# independently admitted test driver. No solver, backend or arithmetic kernels.
using SparseArrays

# Test-only O(n+C) checker; never included by slot-upper.jl or normal factory.
function _check_bg_slots(U::Union{J.BGSlotUpper,J.ProbeBGSlotUpper})::Bool
    n, C = U.n, U.capacity
    n >= 0 && C >= 0 && 0 <= U.live_count <= C || return false
    arrays = (U.value, U.row_id, U.column_id, U.row_prev, U.row_next,
              U.column_prev, U.column_next)
    all(a -> length(a) == C, arrays) || return false
    maps = (U.row_order, U.row_position, U.column_order, U.column_position,
            U.row_head, U.row_tail, U.column_head, U.column_tail)
    all(a -> length(a) == n, maps) || return false
    # No persistent buffer may alias another or the other index's metadata.
    all(i == j || arrays[i] !== arrays[j] for i in 1:7 for j in 1:7) || return false
    all(i == j || maps[i] !== maps[j] for i in 1:8 for j in 1:8) || return false
    all(a !== b for a in arrays for b in maps) || return false
    for j in 1:n
        r, c = U.row_order[j], U.column_order[j]
        1 <= r <= n && 1 <= c <= n || return false
        U.row_position[r] == j && U.column_position[c] == j || return false
    end
    rows, columns, free = falses(C), falses(C), falses(C)
    for rid in 1:n
        s, prev, cid = U.row_head[rid], 0, 0
        while s != 0
            1 <= s <= C && !rows[s] || return false
            U.row_id[s] == rid && cid < U.column_id[s] <= n || return false
            U.row_prev[s] == prev || return false
            rows[s] = true
            cid, prev, s = U.column_id[s], s, U.row_next[s]
        end
        U.row_tail[rid] == prev || return false
    end
    for cid in 1:n
        s, prev, pos = U.column_head[cid], 0, 0
        while s != 0
            1 <= s <= C && !columns[s] || return false
            rid = U.row_id[s]
            U.column_id[s] == cid && 1 <= rid <= n || return false
            pos < U.row_position[rid] <= n && U.column_prev[s] == prev || return false
            columns[s] = true
            pos, prev, s = U.row_position[rid], s, U.column_next[s]
        end
        U.column_tail[cid] == prev || return false
    end
    s = U.free_head
    while s != 0
        1 <= s <= C && !free[s] && !rows[s] && !columns[s] || return false
        U.row_id[s] == 0 && U.column_id[s] == 0 || return false
        U.row_prev[s] == 0 && U.row_next[s] == 0 && U.column_prev[s] == 0 || return false
        U.value[s] == 0.0 || return false
        free[s] = true
        s = U.column_next[s]
    end
    rows == columns && count(rows) == U.live_count || return false
    all(rows[s] != free[s] for s in 1:C) || return false
    return true
end

# Detached logical CSC tokens, preserving explicit -0.0 and NaN payload bits.
function _bg_selected_state(U::Union{J.BGSlotUpper,J.ProbeBGSlotUpper})
    _check_bg_slots(U) || throw(ArgumentError("invalid slot arena"))
    ptr, rows, bits = Int[1], Int[], UInt64[]
    for cid in U.column_order
        s = U.column_head[cid]
        while s != 0
            push!(rows, U.row_position[U.row_id[s]])
            push!(bits, reinterpret(UInt64, U.value[s]))
            s = U.column_next[s]
        end
        push!(ptr, length(rows) + 1)
    end
    return (n=U.n, colptr=ptr, rowval=rows, bits=bits)
end

