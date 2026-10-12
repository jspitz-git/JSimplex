using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
const ROOT=dirname(dirname(pathof(JSimplex)))
const FILE=joinpath(ROOT,"test/bigfloat_integrity_tests.jl")
const SOURCE=read(FILE,String)
Base.include_string(@__MODULE__,first(split(SOURCE,"\n@testset")),FILE)
const MODEL_HELPER="function integrity_model_values" * first(split(split(SOURCE,"function integrity_model_values")[2],"\n@testset"))
Base.include_string(@__MODULE__,MODEL_HELPER,FILE)
const RECORDS=Dict{String,Any}[]
const INITIAL_PRECISION=precision(BigFloat)
const INITIAL_ROUNDING=rounding(BigFloat)
function record_case(problem,options,result,working_precision,mode,interval,original_values)
    gap=integrity_exact(bound_value(only(problem.row_lower)))
    tolerance=integrity_exact(options.primal_tolerance)
    witness=BigFloat[bound_value(only(problem.row_lower))/2]
    push!(RECORDS,Dict("working_precision"=>working_precision,"rounding"=>string(mode),
        "interval"=>interval,"algorithm"=>string(options.algorithm),"presolve"=>options.presolve,
        "scaling"=>string(options.scaling),"status"=>string(result.status),"message"=>result.message,
        "iterations"=>result.statistics.iterations,"refactorizations"=>result.statistics.refactorizations,
        "has_primal"=>!isnothing(result.primal),"has_objective"=>!isnothing(result.objective_value),
        "gap_exact"=>string(gap),"tolerance_exact"=>string(tolerance),
        "options_exact"=>[string(integrity_exact(getfield(options,f))) for f in (:primal_tolerance,:dual_tolerance,:zero_tolerance)],
        "options_precision"=>[precision(getfield(options,f)) for f in (:primal_tolerance,:dual_tolerance,:zero_tolerance)],
        "model_before"=>string.(original_values),"model_after"=>string.(integrity_exact.(integrity_model_values(problem))),
        "model_unchanged"=>isequal(integrity_exact.(integrity_model_values(problem)),original_values),
        "witness_exact"=>string(integrity_exact(only(witness))),
        "exact_witness_column_violation"=>string(gap/2),"exact_witness_row_violation"=>string(gap/2),
        "exact_witness_within_tolerance"=>gap/2<=tolerance,
        "original_witness_certified"=>JSimplex._original_primal_feasible(problem,witness,options.primal_tolerance),
        "strict_gap_exceeds_tolerance"=>gap>tolerance))
end
const TITLE="""@testset "Cross-precision status uses the supplied tolerance" begin"""
const ORIGINAL=TITLE*first(split(split(SOURCE,TITLE)[2],"\n@testset"))
const LOOP="for kind in (:primal, :dual, :zero),"
const PRIMAL_LOOP="for kind in (:primal,),"
const SOLVE="result = @inferred solve(problem; options)"
const RECORD="record_case(problem,options,result,working_precision,mode,interval,original_values)"
@assert count(LOOP,ORIGINAL)==1 && count(SOLVE,ORIGINAL)==1
const SELECTED=replace(replace(ORIGINAL,LOOP=>PRIMAL_LOOP),SOLVE=>SOLVE*"\n                "*RECORD)
@assert replace(replace(SELECTED,PRIMAL_LOOP=>LOOP),SOLVE*"\n                "*RECORD=>SOLVE)==ORIGINAL
@assert !ispath(only(ARGS))
try
    Base.include_string(@__MODULE__,SELECTED,FILE)
finally
    open(only(ARGS),"w") do io
        TOML.print(io,Dict("source"=>pathof(JSimplex),"test_sha256"=>bytes2hex(sha256(SOURCE)),
            "julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH),
            "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
            "oracle_assertions_unchanged"=>true,"selected_primal_only"=>true,
            "globals_restored"=>precision(BigFloat)==INITIAL_PRECISION && rounding(BigFloat)==INITIAL_ROUNDING,
            "records"=>RECORDS))
    end
end
