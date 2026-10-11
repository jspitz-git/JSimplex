# Diagnostic-only entry counts. Load into a separate, guarded Julia process.
include(joinpath(@__DIR__,"../../simplex-time-budget/reproduce/hooks.jl"))
const LONG_HOOKS = vcat(HOOKS, [
    (:refactorize!,"huangfu_hall_factorization.jl"),
    (:_rebuild_pipeline_support!,"hypersparse_pipeline.jl"),
    (:_pipeline_output_support!,"hypersparse_pipeline.jl"),
    (:_copy_pivot_state!,"simplex_pivot.jl"),
    (:_sparse_pricing_workspace!,"sparse_pricing.jl"),
    (:_original_optimality_certified,"dual_simplex.jl"),
])
const LONG_ROLES = (:ftran,:btran,:pricing,:bfrt,:weight_ftran,:weight_btran)
const LONG_COUNTER_LABELS = vcat(string.(first.(LONG_HOOKS)),
    ["finite_value_elements"],
    ["pipeline_$(role)_$(direction)" for role in LONG_ROLES for direction in ("forward","transpose")])

function long_function(source_root,file,prefix)
    source=read(joinpath(source_root,file),String)
    positions=findall(prefix,source)
    length(positions)==1 || throw(ArgumentError("Expected one source hook for $prefix in $file"))
    expression,_=Meta.parse(source,first(only(positions)))
    expression isa Expr && expression.head==:function || error("Invalid function hook: $prefix")
    return expression
end

function install_long_counters!(JS,source_root)
    isdefined(JS,:_lc_counts) && throw(ArgumentError("Long counters already installed"))
    # Validate all source locations before mutating any method in the module.
    expressions=[long_function(source_root,file,"function $(name)(") for (name,file) in LONG_HOOKS]
    values=long_function(source_root,"dual_simplex.jl","function _finite_values(values::Vector")
    count=length(LONG_COUNTER_LABELS)
    Core.eval(JS,:(const _lc_counts=zeros(Int64,$count)))
    for (index,expression) in enumerate(expressions)
        body=expression.args[2]
        if LONG_HOOKS[index][1]==:_pipeline_basis_solve!
            first_role=length(LONG_HOOKS)+2
            # Count requests by declared role/direction. Exceptional refinement
            # calls are reported separately; these are not all raw factor solves.
            role_code=Expr(:block)
            for (role_index,role) in enumerate(LONG_ROLES)
                forward=first_role+2*(role_index-1)
                push!(role_code.args,:(if operation==$(QuoteNode(role))
                    _lc_counts[$forward+Int(transposed)]+=1
                end))
            end
            expression.args[2]=quote
                _lc_counts[$index]+=1
                $role_code
                $body
            end
        else
            expression.args[2]=quote
                _lc_counts[$index]+=1
                $body
            end
        end
        Core.eval(JS,expression)
    end
    body=values.args[2];index=length(LONG_HOOKS)+1
    # This hardware-float implementation visits the entire executed vector.
    # The surrounding && determines which arrays are actually scanned.
    values.args[2]=quote
        _lc_counts[$index]+=length(values)
        $body
    end
    Core.eval(JS,values)
    return nothing
end

reset_long_counters!(JS) = (fill!(JS._lc_counts,0); nothing)
long_counter_rows(JS) = Dict(label=>JS._lc_counts[i] for (i,label) in enumerate(LONG_COUNTER_LABELS))
