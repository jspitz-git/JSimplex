function bg_replay_forward(f, rhs)
    x = similar(rhs)
    JSimplex._backend_forward_solve!(x, f.base, rhs)
    for update in f.updates
        JSimplex._apply_row_update!(x, update)
    end
    JSimplex._upper_backsolve!(x, f.upper)
    out = similar(x)
    out[f.column_order] = x
    return out
end
function bg_replay_transpose(f, rhs)
    x = rhs[f.column_order]
    JSimplex._upper_transpose_solve!(x, f.upper)
    for update in Iterators.reverse(f.updates)
        JSimplex._apply_transposed_row_update!(x, update)
    end
    out = similar(x)
    JSimplex._backend_transpose_solve!(out, f.base, x)
    return out
end

