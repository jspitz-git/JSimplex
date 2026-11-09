using JSimplex, SparseArrays, LinearAlgebra, Logging, SHA, TOML, Test
const JS = JSimplex
const suite = dirname(@__DIR__)
const profile, pricing_arg, arm, input, output = ARGS
const pricing = Symbol(pricing_arg)
const parts = rsplit(profile, "-"; limit=2)
const manager = Symbol(parts[1])
const representation = parts[2]
const normalized = representation == "normalized"
const direct = representation != "production"
const auditing = arm in ("reference-audit", "shadow")
const Constructor = getproperty((huangfu_hall=JS.HuangfuHallFactorization,
    forrest_tomlin=JS.ForrestTomlinFactorization, suhl_suhl=JS.SuhlSuhlFactorization,
    bartels_golub=JS.BartelsGolubFactorization, pfi=JS.PFIFactorization), manager)
@assert pricing in (:dantzig, :steepest_edge)
@assert representation in ("production", "direct", "normalized")
direct && Base.include(JS, joinpath(@__DIR__, "direct.jl"))
const Factor = direct ? Constructor{Float64,JS.TrialLowerBackend} :
    manager == :huangfu_hall ? JS.HuangfuHallFactorization{Float64,JS.Float64UMFPACK,:native} :
    Constructor{Float64,JS.UMFPACKBackend}

const initial_count = Ref(0)
const refactor_count = Ref(0)
const mode_history = Dict{String,Any}[]
const loop_ns = Ref(UInt64(0))
const loop_steps = Ref(0)
const loop_entries = Ref(0)
const loop_depth = Ref(0)

function observe_mode!(f, site, n)
    @assert f isa Factor
    if direct
        @assert isnothing(f.base.fallback)
        @assert f.base.normalize_requested == normalized == !isnothing(f.base.diagonal)
    end
    site == :initial ? (initial_count[] += 1) : (refactor_count[] += 1)
    if auditing
        unit_upper = direct && all(i -> JS._upper_diagonal(f.upper[i],i) == 1.0, eachindex(f.upper))
        if normalized
            @assert unit_upper && length(f.base.diagonal) == n
            @assert all(x -> isfinite(x) && !iszero(x), f.base.diagonal)
        end
        push!(mode_history, Dict("site"=>string(site), "mode"=>representation,
            "dimension"=>n, "unit_upper"=>unit_upper))
    end
    return f
end

function definition(file, name)
    source = read(joinpath(dirname(pathof(JS)),file*".jl"), String)
    positions = findall("function "*name*"(",source)
    @assert length(positions) == 1
    first = Base.first(only(positions))
    _, next = Meta.parse(source, first)
    return source[first:prevind(source,next)]
end
function install_method(name, edits=(); file="dual_simplex", transform=identity)
    source = definition(file,name)
    for (old,new) in edits
        @assert count(old,source) == 1 "Ambiguous patch $name"
        source = replace(source,old=>new)
    end
    Core.eval(JS,transform(Meta.parse(source)))
end

# Both arms check exactly the same initial and subsequently published factor.
@eval JS function _basis_factorization(B::AbstractMatrix{Float64},
    options::SolverOptions{Float64,$(QuoteNode(manager)),:native})
    factor = Main.direct ? _trial_direct_factor(Main.Constructor,B;normalize=Main.normalized) :
        _basis_factorization(B,Val($(QuoteNode(manager))),Val(:native),_native_pivot_policy(options.native_pivot_policy))
    return Main.observe_mode!(factor,:initial,size(B,1))
end
install_method("recompute!", ("                refactorize!(workspace.factorization, B)"=>
    "                Main.observe_mode!(refactorize!(workspace.factorization, B),:refactor,size(B,1))",);file="simplex")
install_method("_discard_candidate!", ("                refactorize!(ws.factorization,basis_matrix(ws))"=>
    "                Main.observe_mode!(refactorize!(ws.factorization,basis_matrix(ws)),:refactor,size(ws.problem.A,1))",);file="simplex_pivot")


install_method("_project_postsolve_basis!", (
    "            refactorize!(workspace.factorization, basis_matrix(workspace))" =>
    "            Main.observe_mode!(refactorize!(workspace.factorization, basis_matrix(workspace)),:refactor,size(workspace.problem.A,1))",);file="solver")

opts(limit; selected=pricing, interval=160, kwargs...) = SolverOptions(algorithm=:dual,
    pricing=selected,basis_update=manager,basis_refactorization=:native,refactorization_interval=interval,
    presolve=false,scaling=:auto,simplex_strategy=:legacy,primal_tolerance=1e-7,dual_tolerance=1e-7,
    time_limit=Inf,iteration_limit=limit,verbose=false,log_level=Logging.Debug;kwargs...)

function time_loop(expr)
    body = expr.args[2]
    expr.args[2] = quote
        local start=time_ns()
        local iter=workspace.iterations
        local level=(Main.loop_depth[]+=1)
        try
            $body
        finally
            if level==1
                Main.loop_ns[]+=time_ns()-start
                Main.loop_steps[]+=workspace.iterations-iter
                Main.loop_entries[]+=1
            end
            Main.loop_depth[]-=1
        end
    end
    return expr
end
function reset_measurement!()
    initial_count[]=refactor_count[]=loop_steps[]=loop_entries[]=0
    loop_ns[]=0
    empty!(mode_history)
end
