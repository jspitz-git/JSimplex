# State/event equivalence under fixed kernel modes; diagnostic method replacements
# are confined to this process. No elapsed-performance evidence is inferred.
using JSimplex,Test,SparseArrays,LinearAlgebra,SHA,TOML,Logging
const JS=JSimplex
@assert Threads.nthreads()==BLAS.get_num_threads()==1
const OUTPUT=only(ARGS)
const PIPELINE=read(joinpath(dirname(pathof(JS)),"hypersparse_pipeline.jl"),String)
function parsed_function(name)
    positions=findall("function $name(",PIPELINE);@assert length(positions)==1
    return first(Meta.parse(PIPELINE,first(only(positions))))
end
Base.include(JS,joinpath(@__DIR__,"pipeline_support_baseline.jl"))
Core.eval(JS,:(const _support_trace_forced_mode=Ref(:sparse)))
mode=parsed_function("_pipeline_mode!")
@assert mode.args[2].head==:block
pushfirst!(mode.args[2].args,:(forced=forced==:auto ? _support_trace_forced_mode[] : forced))
Core.eval(JS,mode)
function state_hash(ws)
    h=SHA.SHA2_256_CTX()
    for values in (ws.basis.basic_indices,ws.basis.states,ws.primal,ws.reduced_costs,ws.costs,ws.pricing_weights)
        SHA.update!(h,reinterpret(UInt8,values))
    end
    return bytes2hex(SHA.digest!(h))
end
function run_case(manager,backend,algorithm,kind,forced)
    JS._support_trace_forced_mode[]=forced
    n=12
    A=kind==:sparse ? spdiagm(0=>ones(n),1=>[isodd(i) ? 0.25 : 0.0 for i in 1:n-1]) :
        sparse(Matrix{Float64}(I,n,n).+1/1024)
    bound=A*ones(n)
    problem=algorithm==:primal ? JS.LinearProblem(A,-ones(n);row_upper=bound) :
        JS.LinearProblem(A,ones(n);row_lower=bound)
    options=JS.SolverOptions(algorithm=algorithm,pricing=:steepest_edge,
        basis_update=manager,basis_refactorization=backend,simplex_strategy=:legacy,
        iteration_limit=200,verbose=false)
    policy=JS.NumericalPolicy(Float64;simplex_strategy=:legacy,hypersparse=true,refactor_timing=false)
    events=SHA.SHA2_256_CTX();counts=Dict{String,Int}();completed=Ref(0)
    observer=(event,ws)->begin
        name=string(event);counts[name]=get(counts,name,0)+1
        SHA.update!(events,codeunits(name*"\n"))
        if event in (:pivot_completed,:flip_completed)
            completed[]+=1
            SHA.update!(events,codeunits(state_hash(ws)))
            SHA.update!(events,reinterpret(UInt8,[ws.iterations,ws.scratch.selected_row,ws.scratch.selected_entering]))
            SHA.update!(events,reinterpret(UInt8,[ws.scratch.last_primal_step,ws.scratch.last_dual_step]))
        end
        nothing
    end
    diagnostics=JS.SimplexDiagnostics(;observer,kernel_timing=true)
    ws=JS.initialize_workspace(problem,options;progress=JS.SimplexProgressContext(problem;numerical_policy=policy,diagnostics))
    entry=state_hash(ws)
    result=JS.run_from_basis!(ws,JS.SimplexRunBudget(ws),policy,()->false)
    @test result.status==JS.OPTIMAL
    @test result.primal≈ones(n)
    @test JS._original_primal_feasible(ws,result.primal)
    @test JS.primal_infeasibility(ws)<=options.primal_tolerance
    @test JS.dual_infeasibility(ws)<=options.dual_tolerance
    @test completed[]>0
    Dict{String,Any}("manager"=>string(manager),"backend"=>string(backend),"algorithm"=>string(algorithm),
        "matrix"=>string(kind),"forced_mode"=>string(forced),"entry_hash"=>entry,"final_hash"=>state_hash(ws),
        "events_hash"=>bytes2hex(SHA.digest!(events)),"event_counts"=>counts,"iterations"=>ws.iterations,
        "refactorizations"=>ws.refactorizations,"kernel_calls"=>Dict(string(k)=>v for (k,v) in diagnostics.kernel_calls))
end
function run_side()
    rows=Dict[]
    @testset "Fixed-mode solver trajectory certificates" begin
        for manager in (:pfi,:huangfu_hall,:forrest_tomlin,:suhl_suhl,:bartels_golub),backend in (:native,:markowitz),
            algorithm in (:primal,:dual),kind in (:sparse,:dense),forced in (:sparse,:dense)
            push!(rows,run_case(manager,backend,algorithm,kind,forced))
        end
    end
    rows
end
records=Dict{String,Any}()
try
    Core.eval(JS,:(_pipeline_output_support!(ws,cache,index,values,canonical::Bool)=
        _pipeline_original_output_support!(ws,cache,index,values)))
    records["control"]=with_logger(NullLogger()) do;Base.invokelatest(run_side);end
    Core.eval(JS,parsed_function("_pipeline_output_support!"))
    records["candidate"]=with_logger(NullLogger()) do;Base.invokelatest(run_side);end
    @testset "Exact paired trajectory equivalence" begin
        @test length(records["control"])==length(records["candidate"])==80
        for (a,b) in zip(records["control"],records["candidate"])
            @test a==b
        end
    end
finally
    records["pipeline_source_hash"]=bytes2hex(sha256(PIPELINE))
    open(io->TOML.print(io,records),OUTPUT,"w")
end
