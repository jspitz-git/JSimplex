function explicit_basis(c, state)
    count_entries = sum(j -> length(c.nz[state[j]]), 1:c.n)
    colptr = Vector{Int}(undef, c.n + 1)
    rows = Vector{Int}(undef, count_entries)
    values = Vector{Float64}(undef, count_entries)
    slot = 1
    for j in 1:c.n
        colptr[j] = slot
        idx = state[j]
        for i in c.nz[idx]
            rows[slot] = i
            values[slot] = c.pool[idx][i]
            slot += 1
        end
    end
    colptr[end] = slot
    return SparseMatrixCSC(c.n, c.n, colptr, rows, values)
end

function replay_local(backend, c, interval::Int, localized::Bool, cold::Bool)
    F = J.BartelsGolubFactorization
    n = c.n
    dir = zeros(n); xf = zeros(n); xb = zeros(n); midpoint = zeros(2n)
    state = collect(1:n)
    trace = Dict{String,Any}[]
    clocks = zeros(UInt64, 6)
    f = nothing; init = ""; completed = 0; refactors = 0
    try
        t = time_ns()
        f = J._direct_lu_factor(F, c.initial, backend, policy(backend); normalize=true)
        clocks[1] += time_ns() - t
        J._direct_mode(f) == :normalized || error("unexpected direct fallback")
        f.base.pivot_policy == policy(backend) || error("policy changed")
        init = cold ? digest_factor(f; initial=true) : ""
        cold && push!(trace, metrics(f, 0, "initial", 0, 0, c.nnzs[1]))
        reference_storage = cold ? J._factor_storage_count(f) : 0
        cold && (trace[end]["storage_ratio_since_refactor"] = 1.)
        reference_growth = cold ? maximum(col -> maximum(abs, col.values; init=0.), f.upper; init=0.) : 0.
        for (k, (j, idx)) in enumerate(c.steps)
            a = c.pool[idx]
            pos = cold ? f.positions[j] : 0
            t = time_ns(); J.forward_solve!(dir, f, a); clocks[2] += time_ns() - t
            all(isfinite, dir) || error("nonfinite entering direction")
            last = cold ? spike_last(f, dir) : -1
            probe = nothing
            if cold
                oracle(c, state, dir, a, c.norms[k]) || error("entering residual at $k")

            end
            t = time_ns()
            if localized
                J._diagnostic_local_bg_replace!(f, dir, j)
            else
                J.replace_column!(f, dir, j)
            end
            clocks[4] += time_ns() - t
            state[j] = idx
            t = time_ns(); J.forward_solve!(xf, f, c.rhs); clocks[2] += time_ns() - t
            t = time_ns(); J.transpose_solve!(xb, f, c.rhs2); clocks[3] += time_ns() - t
            all(isfinite, xf) && all(isfinite, xb) || error("nonfinite solves")
            if cold
                good = oracle(c, state, xf, c.rhs, c.norms[k + 1]) &&
                       oracle(c, state, xb, c.rhs2, c.norms[k + 1], true)
                row = metrics(f, k, "update", pos, last, c.nnzs[k + 1])
                row["storage_ratio_since_refactor"] = row["factor_storage_count"] / max(1, reference_storage)
                u = f.updates[end]
                actual_nonzero = u isa J.BartelsGolubUpdate ?
                    count(s -> !iszero(s.multiplier), u.steps) : count(!iszero, u.multipliers)
                row["new_nonzero_multipliers"] = actual_nonzero
                push!(trace, row)
                good || error("post-update residual at $k")
                isfinite(row["u_max"]) && row["u_max"] <= 1e8 * reference_growth || error("normalized U growth guard at $k")
            end
            completed = k
            if k == 128
                copyto!(midpoint, 1, xf, 1, n)
                copyto!(midpoint, n + 1, xb, 1, n)
            end
            if k % interval == 0 && k < length(c.steps)
                t = time_ns(); B = explicit_basis(c, state); clocks[6] += time_ns() - t
                if cold
                    @test size(B) == (n, n) && nnz(B) == c.nnzs[k + 1]
                    @test all(col -> all(i -> B[i,col] == c.pool[state[col]][i], 1:n), 1:n)
                end
                t = time_ns(); J.refactorize!(f, B); clocks[5] += time_ns() - t
                refactors += 1
                J._direct_mode(f) == :normalized && f.base.pivot_policy == policy(backend) || error("refactor mode/policy changed")
                if cold
                    push!(trace, metrics(f, k, "refactor", 0, 0, c.nnzs[k + 1]))
                    reference_storage = J._factor_storage_count(f)
                    trace[end]["storage_ratio_since_refactor"] = 1.
                    reference_growth = maximum(col -> maximum(abs, col.values; init=0.), f.upper; init=0.)
                end
            end
        end
        all(j -> state[j] == j, 1:n) || error("basis not restored")
        return (ok=true, reason="", step=completed, refactors=refactors, factor=f,
            trace=trace, clocks=clocks, initial=init, dir=dir, xf=xf, xb=xb, middle=midpoint)
    catch err
        err isa InterruptException && rethrow()
        cold || rethrow()
        return (ok=false, reason=sprint(showerror, err), step=completed, refactors=refactors,
            factor=f, trace=trace, clocks=clocks, initial=init, dir=dir, xf=xf, xb=xb, middle=midpoint)
    end
end

