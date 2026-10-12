using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
# Reuse only definitions, not accepted measurements or oracle execution.
const CENSUS=read(joinpath(@__DIR__,"dual_recovery_census.jl"),String)
Base.include_string(@__MODULE__,first(split(CENSUS,"\nrecords=Dict[]")),"dual_recovery_census.jl")
function explicit_dual_retry(ws,stop_requested)
    # Same public entry preparation and exception contract; choose retry as the
    # operation under test instead of relying on a native disagreement to enter it.
    stop=JS._guard_stop_callback(stop_requested)
    stop() && return JS.DualTermination(JS.TIME_LIMIT,"time limit reached")
    JS._prepare_auto_pricing!(ws,:dual;stop) ||
        return JS.DualTermination(JS.TIME_LIMIT,"time limit reached during pricing recovery")
    try
        if !JS._finite_workspace(ws)
            JS._recover_invalid_dse_weights!(ws,stop) || return JS._numerical_failure()
            JS._finite_workspace(ws) || return JS._numerical_failure()
        end
        return JS._measure_basis_iteration!(ws) do
            JS._retry_simplex_step!(ws,stop,:dual,ws.options.dual_tolerance,false,true)
        end
    catch exception
        exception === stop.exception && rethrow()
        JS._is_numerical_exception(exception) || rethrow()
        return JS.DualTermination(JS.NUMERICAL_ERROR,sprint(showerror,exception))
    end
end
# Fresh uniquely named observer helper: one call redirect, no production overwrite.
const OBS=only(filter(x->x isa Expr && x.head==:function &&
    startswith(string(x.args[1]),"observe("),Meta.parseall(first(split(CENSUS,"\nrecords=Dict[]"))).args))
function rewrite_observer!(ex)
    ex isa Expr || return
    if ex.head==:call && ex.args[1]===:observe
        ex.args[1]=:observe_boundary
    elseif ex.head==:call && ex.args[1] == :(JS.dual_iteration!)
        ex.args[1]=:explicit_dual_retry
    end
    for x in ex.args;rewrite_observer!(x);end
end
rewrite_observer!(OBS);Core.eval(@__MODULE__,OBS)
const BASE=TOML.parsefile(ARGS[1])
@assert BASE["test_sha256"]==bytes2hex(sha256(SOURCE))
records=Dict[];controls=Dict[]
@testset "Explicit dual retry boundary qualification" begin
    for manager in MANAGERS,mode in MODES
        old=only(filter(r->r["control"]["manager"]==string(manager) && r["control"]["mode"]==string(mode),BASE["records"]))["observed"]
        new=observe_boundary(manager,mode;record=true)
        keys_to_compare=("before","after","result_type","status","message","wrapped_cause",
                         "cancelled","rejected","numerical_state_unchanged","policy")
        # Saved Float64 TOML preserves selected representations (including -0.0).
        equal=all(isequal(old[k],new[k]) for k in keys_to_compare)
        @test equal
        @test new["counts"]["pivot_rejected"]==1
        @test get(new["counts"],"refactor_pivot",0)==Int(mode==:after_refresh)
        @test get(new["counts"],"pivot_completed",0)==0
        @test get(new["counts"],"bound_flipped",0)==0
        push!(records,Dict("manager"=>string(manager),"mode"=>string(mode),"selected_equal"=>equal,"boundary"=>new))
    end
    for manager in MANAGERS
        p=LinearProblem(sparse(reshape([1.0],1,1)),[1.0];row_lower=[1.0])
        options=SolverOptions(;algorithm=:dual,basis_update=manager,pricing=:dantzig,verbose=false)
        function fresh()
            d=JS.SimplexDiagnostics()
            JS.initialize_workspace(p,options;progress=JS.SimplexProgressContext(p;diagnostics=d))
        end
        direct=fresh();ordinary=fresh()
        @test isnothing(explicit_dual_retry(direct,()->false))
        @test isnothing(JS.dual_iteration!(ordinary,()->false))
        @test isequal(snapshot(direct),snapshot(ordinary))
        @test direct.iterations==1 && direct.primal[1]==1.0
        @test JS._original_primal_feasible(direct,direct.primal[1:1])
        cancelled=fresh();before=snapshot(cancelled)
        @test explicit_dual_retry(cancelled,()->true).status==JS.TIME_LIMIT
        @test isequal(before,snapshot(cancelled))
        failed=fresh();error=SingularException(813);caught=try explicit_dual_retry(failed,()->throw(error)) catch e;e end
        @test caught===error
        invalid=fresh();invalid.primal[1]=NaN
        @test explicit_dual_retry(invalid,()->false).status==JS.NUMERICAL_ERROR
        @test invalid.iterations==0
        push!(controls,Dict("manager"=>string(manager),"direct"=>snapshot(direct),"ordinary"=>snapshot(ordinary),
            "cancel_preserved"=>isequal(before,snapshot(cancelled)),"callback_identity"=>caught===error))
    end
end
@assert !ispath(ARGS[2])
open(ARGS[2],"w") do io
    TOML.print(io,Dict("source"=>pathof(JS),"test_sha256"=>bytes2hex(sha256(SOURCE)),
      "baseline_sha256"=>bytes2hex(sha256(read(ARGS[1]))),"julia_threads"=>Threads.nthreads(),
      "blas_threads"=>BLAS.get_num_threads(),"records"=>records,"controls"=>controls))
end
const REDIRECTS=Ref(0)
function redirect_oracle!(ex)
    ex isa Expr || return
    if ex.head==:call && ex.args[1]==:(JSimplex.dual_iteration!)
        ex.args[1]=:explicit_dual_retry;REDIRECTS[]+=1
    end
    for a in ex.args;redirect_oracle!(a);end
end
for node in NODES;redirect_oracle!(node);end
@assert REDIRECTS[]==4
@testset "Original assertions at explicit retry boundary" begin
    for node in NODES;Core.eval(@__MODULE__,node);end
end
