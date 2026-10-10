using JSimplex, LinearAlgebra, SparseArrays, Serialization, TOML
const JS=JSimplex
function restore_bg(path;fresh=false,diagnostics=nothing)
    d=deserialize(path);p=d.progress
    progress=JS.SimplexProgressContext(time_ns(),p[:objective],p[:objective_constant],p[:scaling],
        p[:iteration_offset],p[:refactorization_offset],diagnostics,p[:numerical_policy])
    w=JS._initialize_workspace_state(d.fields[:problem],d.fields[:options];progress)
    for (name,value) in d.fields
        setfield!(w,name,value)
    end
    if fresh
        w.factorization=JS.BartelsGolubFactorization(JS.basis_matrix(w),Val(:native))
    else
        f=JS.BartelsGolubFactorization(d.base,Val(:native))
        for (name,value) in d.factor
            setfield!(f,name,value)
        end
        w.factorization=f
    end
    w
end
function summary(w)
    Dict("iterations"=>w.iterations,"pinf"=>JS.primal_infeasibility(w),
      "dinf"=>JS.dual_infeasibility(w),"original_costs"=>JS._original_costs_active(w),
      "original_bounds"=>JS._original_bounds_active(w),"algorithm"=>string(w.options.algorithm),
      "primal_tolerance"=>w.options.primal_tolerance,"dual_tolerance"=>w.options.dual_tolerance,
      "driver_mode"=>string(JS._driver_feasibility(w,w.options.dual_tolerance)),
      "updates"=>length(w.factorization.updates))
end
