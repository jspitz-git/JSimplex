# S4-Y OFFLINE diagnostic preparation. UNEXECUTED; no numerical permission.
# A future accepted launcher must reserve the output directory and bind this file.
using JSimplex, SparseArrays, LinearAlgebra, TOML

function retention_matrix(n)
    spdiagm(-1 => fill(-1.0,n-1),0 => fill(4.0,n),1 => fill(-1.0,n-1))
end

function retention_snapshot(backend,label)
    ws = backend.workspace
    isnothing(ws) && error("expected construction workspace")
    Dict{String,Any}(
        "label" => label,
        "dimension" => backend.dimension,
        "row_dictionary_count" => length(ws.rows),
        "column_dictionary_count" => length(ws.columns),
        "row_entries" => sum(length,ws.rows),
        "column_entries" => sum(length,ws.columns),
        "maxima_length" => length(ws.column_maxima),
        "valid_length" => length(ws.column_maxima_valid),
        "active_rows_length" => length(ws.active_rows),
        "active_columns_length" => length(ws.active_columns),
        "workspace_graph_bytes" => Base.summarysize(ws),
        "backend_graph_bytes" => Base.summarysize(backend),
        "has_spare" => !isnothing(backend.spare),
        "lower_pool_count" => length(backend.lower_pool),
        "upper_pool_count" => length(backend.upper_pool),
        "core_rows" => size(backend.core.factors,1),
        "spare_dimension" => isnothing(backend.spare) ? -1 : backend.spare.dimension,
    )
end

function retention_solves(backend,B)
    # Exactly two backend solves per call. Diagnostic products are outside them.
    expected = ones(Float64,size(B,1))
    forward_rhs = B*expected
    transpose_rhs = transpose(B)*expected
    forward = similar(expected)
    transposed = similar(expected)
    JSimplex._backend_forward_solve!(forward,backend,forward_rhs)
    JSimplex._backend_transpose_solve!(transposed,backend,transpose_rhs)
    bound = 64*eps(Float64)
    Dict("forward_unit_solution" => all(i -> abs(forward[i]-expected[i]) <= bound,eachindex(expected)),
         "transpose_unit_solution" => all(i -> abs(transposed[i]-expected[i]) <= bound,eachindex(expected)))
end

function retention_case(kind)
    large = retention_matrix(128)
    small = kind == "sparse" ? retention_matrix(8) : fill(1.0,8,8)
    if kind == "dense"
        for i in 1:8; small[i,i] = 4.0; end
    end
    large_before,small_before = copy(large),copy(small)
    backend = JSimplex.MarkowitzBackend(large)
    saved = JSimplex._copy_backend(backend)
    ws = backend.workspace
    row_owner,column_owner = ws.rows,ws.columns
    maxima_owner,valid_owner = ws.column_maxima,ws.column_maxima_valid
    snapshots = Any[]
    checks = Dict{String,Bool}()
    for (stage,B) in enumerate((large,small,small,large))
        if stage > 1
            backend = JSimplex._refactorize_backend(backend,B)
        end
        label = "stage_"*string(stage)
        push!(snapshots,retention_snapshot(backend,label))
        for (name,value) in retention_solves(backend,B)
            checks[label*"_"*name] = value
        end
        checks[label*"_workspace_owner"] = backend.workspace === ws
        checks[label*"_dictionary_owners"] = ws.rows === row_owner && ws.columns === column_owner
        checks[label*"_maxima_owners"] = ws.column_maxima === maxima_owner && ws.column_maxima_valid === valid_owner
        checks[label*"_retained_dimensions"] = length(ws.rows) == 128 && length(ws.columns) == 128 && length(ws.column_maxima) == 128 && length(ws.column_maxima_valid) == 128
        checks[label*"_input_preserved"] = large == large_before && small == small_before
    end
    # Saved factors share numerical storage but start with no construction scratch.
    for (name,value) in retention_solves(saved,large)
        checks["saved_"*name] = value
    end
    checks["saved_no_workspace_or_spare"] = isnothing(saved.workspace) && isnothing(saved.spare)
    checks["saved_dimension"] = saved.dimension == 128
    # Sparse reset resizes active flags. Dense early return bypasses that reset.
    expected_small_active = kind == "sparse" ? 8 : 128
    checks["small_reset_route"] = all(snapshots[i]["active_rows_length"] == expected_small_active && snapshots[i]["active_columns_length"] == expected_small_active for i in (2,3))
    Dict{String,Any}("kind"=>kind,"snapshots"=>snapshots,"checks"=>checks)
end

function retention_main(output)
    isdir(output) || error("launcher must reserve output directory")
    raw = joinpath(output,"retention.toml")
    ispath(raw) && error("refuse existing raw output")
    cases = Any[]
    errors = String[]
    for kind in ("sparse","dense")
        try
            push!(cases,retention_case(kind))
        catch error
            push!(errors,kind*": "*sprint(showerror,error))
            break # Preserve failure; do not continue a changed or partial schedule.
        end
    end
    all_passed = isempty(errors) && length(cases) == 2 && all(all(values(c["checks"])) for c in cases)
    # Exclusive reservation and invocation binding are future launcher obligations.
    open(raw,"w") do io
        TOML.print(io,Dict("cases"=>cases,"errors"=>errors,"all_passed"=>all_passed))
    end
    all_passed || error("retention qualification failed; preserve output and stop")
end

length(ARGS) == 1 || error("expected one reserved output directory")
retention_main(ARGS[1])
