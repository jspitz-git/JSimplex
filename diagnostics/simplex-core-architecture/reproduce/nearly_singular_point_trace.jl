using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
const ROOT=dirname(dirname(pathof(JSimplex)))
const CONTROL=joinpath(ROOT,"diagnostics/simplex-core-architecture/results/S6-N/census-2-report.toml")
const SAVED=TOML.parsefile(CONTROL)
const BASE=only(filter(x->x["type"]=="Float64",SAVED["records"]))
const EVENTS=Dict{String,Any}[]
const INITIAL_PRECISION=precision(BigFloat)
const INITIAL_ROUNDING=rounding(BigFloat)
exact(x)=Rational{BigInt}(x)
scalar(x)=Dict("exact"=>string(exact(x)),"repr"=>repr(x),
    "precision"=>x isa AbstractFloat ? precision(x) : 0)
function model_record(p)
    Dict("matrix"=>scalar.(vec(Matrix(p.A))),"colptr"=>copy(p.A.colptr),
        "rowval"=>copy(p.A.rowval),"objective"=>scalar.(p.objective),
        "constant"=>scalar(p.objective_constant),"sense"=>string(p.objective_sense),
        "bounds"=>Dict(string(f)=>[isfinite(b) ? scalar(bound_value(b)) : Dict("unbounded"=>true)
            for b in getfield(p,f)] for f in (:row_lower,:row_upper,:column_lower,:column_upper)),
        "domains"=>string.(p.variable_domains),"name"=>p.name,
        "row_names"=>copy(p.row_names),"column_names"=>copy(p.column_names))
end

# Every retained numerical buffer is owned. No solve, certificate, basis-matrix
# getter, factor-property getter or workspace mutation occurs in this observer.
function capture(reason,state)
    length(EVENTS)<512 || error("bounded event capacity exceeded")
    rec=Dict{String,Any}("event"=>string(reason),"state_type"=>string(typeof(state)))
    if state isa JSimplex.SimplexWorkspace
        w=state; p=w.problem; sc=w.scratch; f=w.factorization; scaling=w.progress.scaling
        rec["workspace_id"]=string(objectid(w));rec["model_id"]=string(objectid(p.A))
        rec["matrix_shape"]=collect(size(p.A));rec["matrix_colptr"]=copy(p.A.colptr)
        rec["matrix_rowval"]=copy(p.A.rowval);rec["matrix_nzval"]=copy(p.A.nzval)
        rec["model_objective"]=copy(p.objective);rec["model_constant"]=p.objective_constant
        for field in (:row_lower,:row_upper,:column_lower,:column_upper)
            rec["model_"*string(field)]=copy(getfield(p,field))
        end
        for field in (:costs,:lower,:upper,:primal,:reduced_costs,:pricing_weights,:devex_reference)
            rec[string(field)]=copy(getfield(w,field))
        end
        for field in (:iterations,:refactorizations,:perturbed)
            rec[string(field)]=getfield(w,field)
        end
        rec["basis_indices"]=copy(w.basis.basic_indices);rec["basis_states"]=string.(w.basis.states)
        rec["row_scaling"]=copy(scaling.row_factors);rec["column_scaling"]=copy(scaling.column_factors)
        rec["iteration_offset"]=w.progress.iteration_offset
        rec["refactorization_offset"]=w.progress.refactorization_offset
        rec["options"]=Dict(string(k)=>repr(getfield(w.options,k)) for k in fieldnames(typeof(w.options)))
        policy=w.progress.numerical_policy
        rec["policy"]=Dict(string(k)=>repr(getfield(policy,k)) for k in fieldnames(typeof(policy)))
        rec["staged_workspace"]=w.progress.diagnostics.observer isa JSimplex._StageObserver
        for field in (:row_rhs,:row_solution,:rho,:tau,:tableau_row,:pricing_row)
            rec["scratch_"*string(field)]=copy(getfield(sc,field))
        end
        rec["scratch_role_note"]="Raw scratch may be stale or repurposed; not a certified dual witness"
        rec["pending_factor_update"]=sc.pending_factor_update
        rec["post_iteration"]=string(sc.post_iteration)
        journal=sc.perturbations
        rec["journal_present"]=!isnothing(journal)
        if !isnothing(journal)
            rec["cost_perturbation_active"]=journal.active
            rec["journal_original_costs"]=copy(journal.original_costs)
            rec["bound_perturbation_active"]=!isnothing(journal.bounds) && journal.bounds.active
        end
        rec["factor_type"]=string(typeof(f))
        if f isa JSimplex.PFIFactorization
            rec["base_type"]=string(typeof(f.base))
            rec["updates"]=[Dict("indices"=>copy(e.indices),"values"=>copy(e.values),"pivot_row"=>e.pivot_row) for e in f.updates]
        end
    end
    push!(EVENTS,rec)
    nothing
end
# Encode only after solve. Bound values and floats become exact rational strings;
# integers remain indices/counts, with enum states already converted above.
encode(x::JSimplex.Bound)=isfinite(x) ? Dict("exact"=>string(exact(bound_value(x)))) : Dict("unbounded"=>true)
encode(x::AbstractFloat)=isfinite(x) ? string(exact(x)) : repr(x)
encode(x::AbstractArray)=[encode(v) for v in x]
encode(x::AbstractDict)=Dict(string(k)=>encode(v) for (k,v) in x)
encode(x)=x

scale=ldexp(1f0,-20)
coefficients=Float32[scale scale;scale nextfloat(scale)]
problem=LinearProblem(sparse(Float64.(coefficients)),Float64[0,-1];
    row_lower=Float64[-1,-1],row_upper=Float64[1,1],column_lower=[nothing,nothing])
before=model_record(problem)
options=SolverOptions(Float64)
policy=JSimplex._automatic_numerical_policy(problem,options)
option_record=Dict(string(k)=>repr(getfield(options,k)) for k in fieldnames(typeof(options)))
policy_record=Dict(string(k)=>repr(getfield(policy,k)) for k in fieldnames(typeof(policy)))
@assert before==BASE["model_before"] && option_record==BASE["options"] && policy_record==BASE["policy"]
@assert string(VERSION)==SAVED["julia_version"] && string(Sys.ARCH)==SAVED["arch"]
@assert Threads.nthreads()==BLAS.get_num_threads()==SAVED["julia_threads"]==SAVED["blas_threads"]==1
@assert INITIAL_PRECISION==SAVED["initial_precision"] && string(INITIAL_ROUNDING)==SAVED["initial_rounding"]
@assert !ispath(only(ARGS))
# Exercise non-workspace handling without a numerical solve; isolate probe record.
capture(:certification,nothing)
@assert length(EVENTS)==1 && !haskey(only(EVENTS),"primal")
empty!(EVENTS)
diagnostics=JSimplex.SimplexDiagnostics(observer=capture)
report=Dict{String,Any}("source"=>pathof(JSimplex),"control_sha256"=>bytes2hex(sha256(read(CONTROL))),
    "model_before"=>before,"options"=>option_record,"policy"=>policy_record,
    "julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH),
    "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
    "nonworkspace_probe_passed"=>true,"solver_returned"=>false,
    "coverage"=>"All observer events; owned arrays only; raw scratch role may be stale; no opaque factor, runtime dual witness or backend permutation/scaling capture")
try
    result=JSimplex._solve_diagnosed(problem,diagnostics)
    report["solver_returned"]=true
    report["status"]=string(result.status);report["iterations"]=result.statistics.iterations
    report["refactorizations"]=result.statistics.refactorizations
    report["primal"]=scalar.(result.primal);report["objective"]=scalar(result.objective_value)
    report["endpoint_equal"]=all(report[k]==BASE[k] for k in ("status","iterations","refactorizations","primal","objective"))
    @testset "One observed Float64 solve against saved S6-N endpoint" begin
        @test report["endpoint_equal"]
        @test before==model_record(problem)
        @test !isempty(EVENTS)
        @test diagnostics.kernel_timing==false
        @test precision(BigFloat)==INITIAL_PRECISION && rounding(BigFloat)==INITIAL_ROUNDING
    end
finally
    report["model_after"]=model_record(problem)
    report["globals_preserved"]=precision(BigFloat)==INITIAL_PRECISION && rounding(BigFloat)==INITIAL_ROUNDING
    report["events"]=encode(EVENTS)
    report["counts"]=Dict(string(k)=>v for (k,v) in diagnostics.counts)
    open(only(ARGS),"w") do io
        TOML.print(io,report)
    end
end
