using GLPK
using JSimplex: OPTIMAL, INFEASIBLE, UNBOUNDED, MIN_SENSE, read_mps

function glpk_status(status)
    status == GLPK.GLP_OPT && return OPTIMAL
    status == GLPK.GLP_NOFEAS && return INFEASIBLE
    status == GLPK.GLP_UNBND && return UNBOUNDED
    return nothing
end

function write_glpk_mps_view(output, path)
    before_rows = true
    pending_metadata = false
    open(path) do input
        for line in eachline(input)
            # Metadata occurs only before ROWS. Keep structural records intact,
            # including columns/rows named OBJSENSE or OBJNAME.
            if before_rows
                text = strip(replace(line, r"(?<!\S)\$.*$" => ""))
                if !isempty(text) && !startswith(text, '*')
                    words = split(text)
                    if pending_metadata
                        pending_metadata = false
                        continue
                    elseif first(words) in ("OBJSENSE", "OBJSEN", "OBJNAME")
                        pending_metadata = length(words) == 1
                        continue
                    elseif first(words) == "ROWS"
                        before_rows = false
                    end
                end
            end
            println(output, line)
        end
    end
end

function set_glpk_objective!(problem, native, path)
    count = GLPK.glp_get_num_cols(problem)
    count == length(native.objective) || throw(ErrorException(
        "GLPK column count differs from the native model for '$path'."))
    native_columns = Dict(name => index for (index, name) in enumerate(native.column_names))
    length(native_columns) == count || throw(ErrorException(
        "GLPK reference needs unique native column names for '$path'."))
    seen = Set{String}()
    for column in 1:count
        name_pointer = GLPK.glp_get_col_name(problem, column)
        name_pointer == C_NULL && throw(ErrorException("GLPK returned an unnamed column for '$path'."))
        name = unsafe_string(name_pointer)
        haskey(native_columns, name) && !(name in seen) || throw(ErrorException(
            "GLPK column '$name' cannot be matched uniquely to the native model for '$path'."))
        push!(seen, name)
        GLPK.glp_set_obj_coef(problem, column, native.objective[native_columns[name]])
    end
    GLPK.glp_set_obj_dir(problem, native.objective_sense == MIN_SENSE ? GLPK.GLP_MIN : GLPK.GLP_MAX)
    # JSimplex reverses the objective RHS sign; raw GLPK MPS import does not.
    GLPK.glp_set_obj_coef(problem, 0, native.objective_constant)
end

"""
Solve the continuous relaxation with GLPK using the native objective semantics.
GLPK independently reads constraints and bounds from a temporary MPS view with
unsupported objective metadata removed. The selected objective, sense, and
constant come from public `read_mps`, matched by validated column names.
The source remains unchanged; temporary files and the C problem are released.
"""
function solve_with_glpk(path::AbstractString)
    native = try
        read_mps(path)
    catch exception
        exception isa InterruptException && rethrow()
        throw(ErrorException("GLPK reference could not read '$path' using the native MPS parser: $(sprint(showerror, exception))"))
    end
    problem = GLPK.glp_create_prob()
    problem == C_NULL && throw(ErrorException("GLPK could not allocate a problem for '$path'."))
    try
        code = mktemp() do normalized_path, output
            write_glpk_mps_view(output, path)
            close(output)
            GLPK.glp_read_mps(problem, GLPK.GLP_MPS_FILE, C_NULL, normalized_path)
        end
        code == 0 || throw(ErrorException("GLPK could not read '$path' (code $code)."))
        set_glpk_objective!(problem, native, path)
        solve_code = GLPK.glp_simplex(problem, C_NULL)
        solve_code == 0 || throw(ErrorException("GLPK could not solve '$path' (code $solve_code)."))
        status = GLPK.glp_get_status(problem)
        return (status=glpk_status(status), raw_status=status,
                objective=status == GLPK.GLP_OPT ? GLPK.glp_get_obj_val(problem) : nothing)
    finally
        GLPK.glp_delete_prob(problem)
    end
end
