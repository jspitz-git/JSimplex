include(joinpath(@__DIR__, "reused-prefix.jl"))

# Diagnostic only: a fresh graph is built on each COLD call. This is not an
# admitted hot eligibility implementation. Exact structural zeros only.
function structural_probe(upper, spike, position)
    n = length(upper)
    if !isfinite(spike[position]) || iszero(spike[position])
        return Dict{String,Any}("supported" => false, "possible" => false,
            "reason" => "zero or nonfinite spike diagonal")
    end
    rows = [Int[] for _ in 1:n]
    scanned = 0
    diagonal_ok = trues(n)
    for j in 1:n
        found = false
        column = upper[j]
        for k in eachindex(column.values)
            i = column.indices[k]
            v = column.values[k]
            scanned += 1
            if i == j
                found = isfinite(v) && !iszero(v)
            end
            iszero(v) || push!(rows[i], j)
        end
        diagonal_ok[j] = found
    end
    all(diagonal_ok) || return Dict{String,Any}("supported" => false,
        "possible" => false, "reason" => "invalid old diagonal")
    reached = falses(n)
    stack = Int[position]
    reached[position] = true
    edges = 0
    while !isempty(stack)
        i = pop!(stack)
        for j in rows[i]
            edges += 1
            if !reached[j]
                reached[j] = true
                push!(stack, j)
            end
        end
    end
    possible = all(i -> i == position || !reached[i] || iszero(spike[i]), 1:n)
    # Independent acyclicity check on the actually replaced column pattern.
    # Diagonal self-edges are ignored. No cancellation/drop tolerance is used.
    indegree = zeros(Int, n)
    for i in 1:n
        for j in rows[i]
            j != position && j != i && (indegree[j] += 1)
        end
        i != position && !iszero(spike[i]) && (indegree[position] += 1)
    end
    queue = findall(iszero, indegree)
    removed = 0
    while !isempty(queue)
        i = pop!(queue)
        removed += 1
        for j in rows[i]
            if j != position && j != i
                indegree[j] -= 1
                indegree[j] == 0 && push!(queue, j)
            end
        end
        if i != position && !iszero(spike[i])
            indegree[position] -= 1
            indegree[position] == 0 && push!(queue, position)
        end
    end
    possible == (removed == n) || error("reachability/topological criteria disagree")
    last = something(findlast(!iszero, spike), 0)
    union_columns = falses(n)
    if last >= position
        for i in position:last, j in rows[i]
            union_columns[j] = true
        end
    end
    return Dict{String,Any}("supported" => true, "possible" => possible,
        "reason" => "zero-free-diagonal structural criterion", "topological_agreement" => true,
        "graph_entries_scanned" => scanned, "reach_edges_visited" => edges,
        "reach_nodes" => count(reached), "pre_rotation_row_union_columns" => count(union_columns),
        "suffix_columns" => n - position + 1, "rotation_span" => last - position)
end

function prepared_spike(f, dir)
    cache = f.row_cache.prepared
    cache === nothing && error("missing prepared spike")
    for entry in cache.entries
        entry.destination === dir && isequal(entry.direction, dir) && return entry.spike
    end
    error("prepared spike provenance mismatch")
end

# Assemble every scheduled new basis INSIDE the whole timing window. This
# pays row/value/column-pointer copies and allocation for each extra refactor.
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

function replay_interval(F::Type, backend, c, interval::Int, cold::Bool)
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
                pt = @timed structural_probe(f.upper, prepared_spike(f, dir), pos)
                probe = pt.value
                probe["seconds"] = pt.time
                probe["bytes"] = pt.bytes
                probe["events"] = Base.gc_alloc_count(pt.gcstats)
                probe["compile_seconds"] = pt.compile_time
                probe["recompile_seconds"] = pt.recompile_time
            end
            t = time_ns(); J.replace_column!(f, dir, j); clocks[4] += time_ns() - t
            state[j] = idx
            t = time_ns(); J.forward_solve!(xf, f, c.rhs); clocks[2] += time_ns() - t
            t = time_ns(); J.transpose_solve!(xb, f, c.rhs2); clocks[3] += time_ns() - t
            all(isfinite, xf) && all(isfinite, xb) || error("nonfinite solves")
            if cold
                good = oracle(c, state, xf, c.rhs, c.norms[k + 1]) &&
                       oracle(c, state, xb, c.rhs2, c.norms[k + 1], true)
                row = metrics(f, k, "update", pos, last, c.nnzs[k + 1])
                row["storage_ratio_since_refactor"] = row["factor_storage_count"] / max(1, reference_storage)
                row["permutation_probe"] = probe
                u = f.updates[end]
                actual_nonzero = u isa J.BartelsGolubUpdate ?
                    count(s -> !iszero(s.multiplier), u.steps) : count(!iszero, u.multipliers)
                row["new_nonzero_multipliers"] = actual_nonzero
                row["pure_permutation_with_actual_elimination"] = probe["supported"] && probe["possible"] && actual_nonzero > 0
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

function save_results(data)
    open(joinpath(D, "results-1.toml"), "w") do io
        TOML.print(io, data)
    end
end

function run_options()
    data = Dict{String,Any}("cold" => Any[], "windows" => Any[], "preparation" => Any[],
        "scope" => "structural feasibility only, no permutation implementation or production promotion")
    intervals = (128, 64, 32, 16)
    # User requested SS first. Other managers follow only after its complete pass.
    for manager in (2, 1, 3)
        F = MANAGERS[manager]
        for kind in ("band", "blocks", "sparse", "dense")
            prep = @timed makecase(kind)
            c = prep.value; before = inputhash(c)
            push!(data["preparation"], Dict("manager" => LABELS[manager], "fixture" => kind,
                "seconds" => prep.time, "bytes" => prep.bytes, "events" => Base.gc_alloc_count(prep.gcstats),
                "compile_seconds" => prep.compile_time))
            for backend in (Val(:native), Val(:markowitz))
                bname = string(typeof(backend).parameters[1])
                refs = Any[]; eligible = true
                for interval in intervals
                    t = @timed replay_interval(F, backend, c, interval, true)
                    r = t.value
                    @test r.ok
                    @test inputhash(c) == before
                    eligible &= r.ok
                    signature = r.factor === nothing ? "" : digest_factor(r.factor)
                    push!(refs, (initial=r.initial, signature=signature, dir=copy(r.dir),
                        xf=copy(r.xf), xb=copy(r.xb), middle=copy(r.middle)))
                    push!(data["cold"], Dict("manager" => LABELS[manager], "fixture" => kind,
                        "backend" => bname, "interval" => interval, "ok" => r.ok, "reason" => r.reason,
                        "updates" => r.step, "refactors" => r.refactors, "seconds" => t.time,
                        "bytes" => t.bytes, "events" => Base.gc_alloc_count(t.gcstats),
                        "initial_factor_hash" => r.initial, "final_factor_hash" => signature, "trace" => r.trace))
                    r = nothing; t = nothing
                    save_results(data)
                end
                @test all(r -> r.initial == refs[1].initial, refs)
                if eligible
                    GC.gc()
                    for repetition in 0:5
                        order = mod1.(collect(1:4) .+ repetition, 4)
                        for i in order
                            interval = intervals[i]
                            t = @timed replay_interval(F, backend, c, interval, false)
                            r = t.value
                            @test r.ok && digest_factor(r.factor) == refs[i].signature
                            @test isequal((r.dir, r.xf, r.xb, r.middle), (refs[i].dir, refs[i].xf, refs[i].xb, refs[i].middle))
                            @test oracle(c, collect(1:c.n), r.xf, c.rhs, c.norms[end]) &&
                                  oracle(c, collect(1:c.n), r.xb, c.rhs2, c.norms[end], true)
                            @test inputhash(c) == before
                            @test r.refactors == div(256, interval) - 1
                            if repetition > 0
                                @test t.compile_time == t.recompile_time == 0
                            end
                            push!(data["windows"], Dict("manager" => LABELS[manager], "fixture" => kind,
                                "backend" => bname, "interval" => interval, "repetition" => repetition,
                                "warm" => repetition == 0, "seconds" => t.time, "bytes" => t.bytes,
                                "events" => Base.gc_alloc_count(t.gcstats), "gc_seconds" => t.gctime,
                                "compile_seconds" => t.compile_time, "recompile_seconds" => t.recompile_time,
                                "construct_seconds" => r.clocks[1]/1e9, "ftran_seconds" => r.clocks[2]/1e9,
                                "btran_seconds" => r.clocks[3]/1e9, "update_seconds" => r.clocks[4]/1e9,
                                "refactor_seconds" => r.clocks[5]/1e9, "assembly_seconds" => r.clocks[6]/1e9,
                                "updates" => r.step, "refactors" => r.refactors,
                                "retained_bytes" => Base.summarysize(r.factor)))
                            r = nothing; t = nothing
                        end
                    end
                end
                save_results(data)
                println("COMPLETED ", LABELS[manager], "/", kind, "/", bname, " eligible=", eligible)
                flush(stdout)
            end
        end
    end
end

@testset "Independent structural predicate sanity" begin
    # Identity plus a subdiagonal spike is a DAG; adding the reverse old-U edge
    # creates a cycle. Zero diagonal is deliberately unsupported, not impossible.
    upper = [(indices=[1], values=[1.]), (indices=[2], values=[1.])]
    @test structural_probe(upper, [1., 1.], 1)["possible"]
    cycle = [(indices=[1], values=[1.]), (indices=[1,2], values=[1.,1.])]
    @test !structural_probe(cycle, [1., 1.], 1)["possible"]
    @test !structural_probe(upper, [0., 1.], 1)["supported"]
    @test upper == [(indices=[1], values=[1.]), (indices=[2], values=[1.])]
end
@testset "SS then FT BG structural options" begin
    run_options()
end
