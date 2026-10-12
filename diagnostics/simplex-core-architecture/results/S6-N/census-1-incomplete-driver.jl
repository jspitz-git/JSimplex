using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
const ROOT=dirname(dirname(pathof(JSimplex)))
const FILE=joinpath(ROOT,"test/solver_tests.jl")
const SOURCE=read(FILE,String)
const RECORDS=Dict{String,Any}[]
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
function record_case(problem::LinearProblem{T},result,before) where T
    options=SolverOptions(T) # Reconstruct documented defaults; not passed to solve.
    policy=JSimplex._automatic_numerical_policy(problem,options)
    A=exact.(Matrix(problem.A)); s=A[1,1]; d=A[2,2]-s
    determinant=A[1,1]*A[2,2]-A[1,2]*A[2,1]
    optimum=-2/d
    optimum_primal=[-1/s-2/d,2/d]
    dual=[1/d,-1/d]
    t=exact(options.primal_tolerance)
    rec=Dict{String,Any}("type"=>string(T),"status"=>string(result.status),
        "message"=>result.message,"iterations"=>result.statistics.iterations,
        "refactorizations"=>result.statistics.refactorizations,
        "has_primal"=>!isnothing(result.primal),"has_objective"=>!isnothing(result.objective_value),
        "options"=>Dict(string(f)=>repr(getfield(options,f)) for f in fieldnames(typeof(options))),
        "policy"=>Dict(string(f)=>repr(getfield(policy,f)) for f in fieldnames(typeof(policy))),
        "tolerances_exact"=>Dict(string(f)=>string(exact(getfield(options,f))) for f in
            (:primal_tolerance,:dual_tolerance,:zero_tolerance)),
        "model_before"=>before,"model_after"=>model_record(problem),
        "model_unchanged"=>before==model_record(problem),
        "determinant_exact"=>string(determinant),"delta_exact"=>string(d),
        "strict_optimum_exact"=>string(optimum),"strict_primal_exact"=>string.(optimum_primal),
        "strict_rows_exact"=>string.(A*optimum_primal),"dual_exact"=>string.(dual),
        "dual_stationarity_exact"=>string.(exact.(problem.objective)-transpose(A)*dual),
        "tolerance_objective_lower_exact"=>string(-2*(1+t)/d),
        "globals_unchanged_after_solve"=>precision(BigFloat)==INITIAL_PRECISION && rounding(BigFloat)==INITIAL_ROUNDING)
    if !isnothing(result.primal)
        x=exact.(result.primal); rows=A*x
        objective=dot(exact.(problem.objective),x)+exact(problem.objective_constant)
        violations=max.(abs.(rows).-1,0)
        # A separately supplied analytic witness, NOT the runtime basis/dual.
        basis=Basis([1,2],[BASIC,BASIC,AT_LOWER,AT_UPPER])
        merge!(rec,Dict("primal"=>scalar.(result.primal),"objective"=>scalar(result.objective_value),
            "rows_exact"=>string.(rows),"row_violations_exact"=>string.(violations),
            "objective_from_primal_exact"=>string(objective),
            "objective_gap_exact"=>string(exact(result.objective_value)-optimum),
            "objective_matches_primal_exact"=>exact(result.objective_value)==objective,
            "strict_feasible"=>all(iszero,violations),"tolerance_feasible_exact"=>all(v->v<=t,violations),
            "distance_to_priced_bounds_exact"=>string.(abs.(rows-[-1,1])),
            "analytic_complementarity_within_tolerance"=>all(v->v<=t,abs.(rows-[-1,1])),
            "original_primal_certificate"=>JSimplex._original_primal_feasible(problem,result.primal,options.primal_tolerance),
            "analytic_witness_certificate"=>JSimplex._original_witness_certified(problem,options,basis,result.primal,T.(dual))))
    end
    push!(RECORDS,rec)
end
const TITLE="""@testset "A nearly singular bounded model has no recession ray" begin"""
const ORIGINAL=TITLE*first(split(split(SOURCE,TITLE)[2],"\n@testset"))
const SOLVE="result = @inferred solve(problem)"
const INSERT="before = model_record(problem)\n        "*SOLVE*"\n        record_case(problem,result,before)"
@assert count(SOLVE,ORIGINAL)==1
const SELECTED=replace(ORIGINAL,SOLVE=>INSERT)
@assert replace(SELECTED,INSERT=>SOLVE)==ORIGINAL
@assert !ispath(only(ARGS))
try
    Base.include_string(@__MODULE__,SELECTED,FILE)
finally
    open(only(ARGS),"w") do io
        TOML.print(io,Dict("source"=>pathof(JSimplex),"test_sha256"=>bytes2hex(sha256(SOURCE)),
            "julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH),
            "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
            "oracle_assertions_unchanged"=>true,"default_public_solve_unchanged"=>true,
            "certificate_scope"=>"Postsolve original primal and separately supplied analytic dual/basis; no runtime witness capture",
            "initial_precision"=>INITIAL_PRECISION,"initial_rounding"=>string(INITIAL_ROUNDING),
            "globals_restored"=>precision(BigFloat)==INITIAL_PRECISION && rounding(BigFloat)==INITIAL_ROUNDING,
            "records"=>RECORDS))
    end
end
