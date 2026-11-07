using JSimplex, SparseArrays, LinearAlgebra, Logging, SHA, TOML, Test
const JS=JSimplex
const suite=realpath(joinpath(@__DIR__,".."))
const root=dirname(dirname(suite))
const variant,arm,input,output=ARGS
const names=rsplit(variant,"_";limit=2)
const manager=names[2]
const basis_update=Symbol(names[1])
const Constructor=getproperty((suhl_suhl=JS.SuhlSuhlFactorization,bartels_golub=JS.BartelsGolubFactorization), basis_update)
@assert manager in ("direct","normalized")
@assert arm in ("unit","reference-audit","shadow","reference","candidate")
const normalized=manager=="normalized"
const audit=arm in ("reference-audit","shadow")
const direct_source=joinpath(root,"diagnostics/runtime-full-chain-comparison/ss-bg-breakdown/reproduce/direct.jl")
Base.include(JS,direct_source)
const Factor=Constructor{Float64,JS.TrialLowerBackend}
const initial_count=Ref(0)
const refactor_count=Ref(0)
const mode_history=Vector{NamedTuple{(:site,:mode,:dimension,:unit_upper),Tuple{String,String,Int,Bool}}}()
const loop_ns=Ref(UInt64(0))
const loop_steps=Ref(0)
const loop_entries=Ref(0)
const loop_depth=Ref(0)

actual_mode(f)=:ordinary
actual_mode(f::Factor)=!isnothing(f.base.fallback) ? :fallback : isnothing(f.base.diagonal) ? :direct : :normalized
const requested=Symbol(manager)
eligible(f)=f isa Factor && f.base.normalize_requested==normalized && actual_mode(f)===requested

function observe_mode!(f,site)
    actual=actual_mode(f)
    if !eligible(f)
        open(io->TOML.print(io,Dict("site"=>string(site),"actual"=>string(actual),
            "requested"=>manager,"type"=>string(typeof(f)))),
            output*".mode-failure.toml","w")
        error("Unexpected published $variant mode: $actual")
    end
    if site==:initial
        initial_count[]+=1
    else
        refactor_count[]+=1
    end
    if audit
        n=length(f.upper)
        @assert size(f.base.lower)==(n,n) && length(f.base.row_order)==length(f.base.scaling)==n
        unit_upper=all(i->JS._upper_diagonal(f.upper[i],i)==1.0,eachindex(f.upper))
        if normalized
            @assert length(f.base.diagonal)==n && all(x->isfinite(x)&&!iszero(x),f.base.diagonal) && unit_upper
        end
        push!(mode_history,(site=string(site),mode=string(actual),dimension=n,unit_upper=unit_upper))
    end
    return f
end

# The factory and the already-published live refactor are checked separately.
@eval JS function _basis_factorization(B::AbstractMatrix{Float64},options::SolverOptions{Float64,$(QuoteNode(basis_update)),:native})
    options.simplex_strategy==:legacy || return $Constructor(B)
    return Main.observe_mode!(_trial_direct_factor($Constructor,B;normalize=Main.normalized),:initial)
end
@eval JS function refactorize!(f::$Factor, B::AbstractMatrix{Float64})
    invoke(refactorize!,Tuple{TrialDirectFactor,AbstractMatrix{Float64}},f,B)
    return Main.observe_mode!(f,:refactor)
end

const dual_source=read(joinpath(dirname(pathof(JS)),"dual_simplex.jl"),String)
function install_method(name, edits=(); timed_loop=false)
    at=first(only(findall("function "*name*"(",dual_source)))
    _,last=Meta.parse(dual_source,at)
    body=dual_source[at:prevind(dual_source,last)]
    for (from,to) in edits
        @assert count(from,body)==1 "Cannot identify unique $name patch site: $from"
        body=replace(body,from=>to)
    end
    ex=Meta.parse(body)
    if timed_loop
        old=ex.args[2]
        ex.args[2]=quote
            local start=time_ns()
            local iter=workspace.iterations
            local level=(Main.loop_depth[]+=1)
            try
                $old
            finally
                if level==1
                    Main.loop_ns[]+=time_ns()-start
                    Main.loop_steps[]+=workspace.iterations-iter
                    Main.loop_entries[]+=1
                end
                Main.loop_depth[]-=1
            end
        end
    end
    Core.eval(JS,ex)
end
if arm in ("unit","shadow","candidate")
    # Exactly one eligibility condition changes. All stop/policy/alias checks stay in the shared code.
    install_method("_can_reuse_dual_checks",("ws.factorization isa _NativeDualCheckFactor"=>"Main.eligible(ws.factorization)",))
end
if audit
    include(joinpath(root,"diagnostics/hh-local-check-reuse/reproduce/audit.jl"))
    install_audit()
    # Recompute the pre-existing clock-only entry reuse in BOTH arms as well.
    needle="        if !Validated && !_finite_workspace(workspace)"
    install_method("_dual_iteration_entry!",(needle=>"""        if Validated
            @assert _finite_workspace(workspace)
            Main.counted(stop_requested isa _StopCallback{<:_BasisBudgetStop} ? "driver_entry" : "common_entry")
        end
$needle""",))
end
if arm=="shadow"
    install_method("_dual_iteration_unchecked!",(
        "                    row_failed = false"=>"                    Main.shadow_row(workspace,rho,leaving_row)\n                    row_failed = false",
        "    _replace_pivot_column!(workspace, tableau_column, leaving_row;"=>"    Main.before_publish(workspace,changed_primal_index)\n    _replace_pivot_column!(workspace, tableau_column, leaving_row;"))
    needle="        isfinite(workspace.primal[changed_primal_index]) || return _numerical_failure()"
    install_method("_dual_after_iteration!",(needle=>"        Main.shadow_finite(workspace,changed_primal_index)\n"*needle,))
    install_method("_dual_optimize!",("        if !previous_step_checked"=>"        if previous_step_checked\n            @assert _finite_workspace(workspace)\n            Main.counted(\"from_last_pivot\")\n        else",);timed_loop=true)
else
    install_method("_dual_optimize!";timed_loop=true)
end

opts(limit;interval=160)=SolverOptions(algorithm=:dual,pricing=:devex,basis_update=basis_update,basis_refactorization=:native,
    refactorization_interval=interval,presolve=false,scaling=:auto,simplex_strategy=:legacy,
    primal_tolerance=1e-7,dual_tolerance=1e-7,time_limit=Inf,iteration_limit=limit,verbose=false,log_level=Logging.Debug)

function unit()
    @testset "Actual direct backend and eligibility" begin
        B=sparse([2.0 0.0; 0.0 3.0])
        f=JS._basis_factorization(B,opts(100))
        @test eligible(f) && initial_count[]==1
        @test JS.refactorize!(f,B)===f && eligible(f) && refactor_count[]==1
        @test !eligible(Constructor(B))
        @test !eligible(JS._trial_direct_factor(Constructor,B;normalize=!normalized))
        b=f.base
        # Both normalized-to-direct downgrade and fallback must lose authority.
        f.base=JS.TrialLowerBackend(b.lower,b.row_order,b.scaling,b.divide_scaling,nothing,true,nothing,b.work)
        @test !eligible(f)
        f.base=JS.TrialLowerBackend(b.lower,b.row_order,b.scaling,b.divide_scaling,b.diagonal,normalized,JS._factorize_basis(B),b.work)
        @test actual_mode(f)==:fallback && !eligible(f)
        p=LinearProblem(sparse(reshape([1.0],1,1)),[1.0];row_lower=[1.0])
        w=JS.initialize_workspace(p,opts(10;interval=1))
        stop=JS._guard_stop_callback(JS._SolveDeadline(time_ns(),Inf))
        @test JS._can_reuse_dual_checks(w,stop)
        @test !JS._can_reuse_dual_checks(w,JS._guard_stop_callback(()->false))
        @test !JS._can_reuse_corrected_row(w,stop,w.scratch.rho,w.scratch.rho)
        @test JS._dual_optimize!(w,stop).status==JS.OPTIMAL && w.refactorizations==1 && eligible(w.factorization)
        diag=JS.SimplexDiagnostics(;observer=(ev,w)->ev==:pivot_completed && (w.pricing_weights[1]=0.0))
        observed=JS.initialize_workspace(p,opts(10);progress=JS.SimplexProgressContext(p;diagnostics=diag))
        @test !JS._can_reuse_dual_checks(observed,stop)
        @test JS.dual_iteration!(observed,stop).status==JS.NUMERICAL_ERROR
    end
end

function run()
    @assert Sys.ARCH==:aarch64 && Threads.nthreads()==BLAS.get_num_threads()==1
    if arm=="unit"; unit(); return; end
    expected=TOML.parsefile(joinpath(root,"diagnostics/runtime-full-chain-comparison/ss-bg-breakdown/results/jsimplex-$variant-160-repeat1.toml"))
    @assert bytes2hex(open(sha256,input))==expected["input_sha256"]
    lp=read_mps(input); af=read_mps(joinpath(root,"diagnostics/ft-local-incidence/reproduce/afiro.mps"))
    @assert solve(af;options=opts(typemax(Int)),relax_integrality=true).status==JS.OPTIMAL
    @assert solve(lp;options=opts(100),relax_integrality=true).status==JS.ITERATION_LIMIT
    audit && reset_audit!()
    initial_count[]=refactor_count[]=loop_steps[]=loop_entries[]=0;loop_ns[]=0;empty!(mode_history)
    GC.gc()
    t=@timed solve(lp;options=opts(typemax(Int)),relax_integrality=true)
    r=t.value
    d=Dict("variant"=>variant,"manager"=>manager,"arm"=>arm,"status"=>string(r.status),"message"=>r.message,
        "original_feasible"=>r.status==JS.OPTIMAL && JS._original_primal_feasible(lp,r.primal,1e-7),
        "objective_bits"=>isnothing(r.objective_value) ? "" : string(reinterpret(UInt64,r.objective_value),base=16),
        "primal_sha"=>isnothing(r.primal) ? "" : bytes2hex(sha256(reinterpret(UInt8,r.primal))),
        "iterations"=>r.statistics.iterations,"refactors"=>r.statistics.refactorizations,"mode_initial"=>initial_count[],
        "mode_refactors"=>refactor_count[],"mode"=>manager,"loop"=>loop_ns[]/1e9,"steps"=>loop_steps[],"entries"=>loop_entries[],
        "seconds"=>t.time,"bytes"=>t.bytes,"gc"=>t.gctime,"compile"=>t.compile_time,"threads"=>Threads.nthreads(),
        "blas_threads"=>BLAS.get_num_threads(),"arch"=>string(Sys.ARCH),"options"=>string(opts(typemax(Int))),
        "input_sha"=>expected["input_sha256"])
    open(io->TOML.print(io,d),output,"w")
    if audit
        report=audit_report()
        report["modes"]=[Dict(string(k)=>v for (k,v) in pairs(row)) for row in mode_history]
        open(io->TOML.print(io,report),output*".audit.toml","w")
    end
    @assert d["original_feasible"] && loop_depth[]==0 && 0<d["loop"]<=t.time
end
run()
