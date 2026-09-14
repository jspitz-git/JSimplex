using GLPK
using JSimplex: OPTIMAL, INFEASIBLE, UNBOUNDED

function glpk_status(status)
    status == GLPK.GLP_OPT && return OPTIMAL
    status == GLPK.GLP_NOFEAS && return INFEASIBLE
    status == GLPK.GLP_UNBND && return UNBOUNDED
    return nothing
end

"""Solve the continuous relaxation with GLPK; always release the C problem."""
function solve_with_glpk(path::AbstractString)
    problem = GLPK.glp_create_prob()
    problem == C_NULL && throw(ErrorException("GLPK could not allocate a problem for '$path'."))
    try
        code = GLPK.glp_read_mps(problem, GLPK.GLP_MPS_FILE, C_NULL, path)
        code == 0 || throw(ErrorException("GLPK could not read '$path' (code $code)."))
        solve_code = GLPK.glp_simplex(problem, C_NULL)
        solve_code == 0 || throw(ErrorException("GLPK could not solve '$path' (code $solve_code)."))
        status = GLPK.glp_get_status(problem)
        return (status=glpk_status(status), raw_status=status,
                objective=status == GLPK.GLP_OPT ? GLPK.glp_get_obj_val(problem) : nothing)
    finally
        GLPK.glp_delete_prob(problem)
    end
end
