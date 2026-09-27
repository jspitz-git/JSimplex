using JSimplex, Serialization, TOML, LinearAlgebra
report=TOML.parsefile(popfirst!(ARGS))
for path in ARGS
    data=deserialize(path)
    for key in (:run_id,:source_revision,:input_sha256,:julia,:architecture)
        @assert getproperty(data,key)==report[string(key)]
    end
    println("PROVENANCE_OK file=",basename(path)," iteration=",data.iteration,
        " event=",data.event," updated_columns=",length(data.factorization.updates),
        " prior_basis=",hasproperty(data,:prior_basis),
        " native_numeric=",!isnothing(data.native_numeric))
    options=data.options
    @assert options.basis_update==Symbol(report["basis_update"])
    println("OPTIONS algorithm=",options.algorithm," strategy=",options.simplex_strategy,
        " pricing=",options.pricing," refactorization=",options.basis_refactorization,
        " configured_interval=",options.refactorization_interval,
        " primal_tolerance=",options.primal_tolerance," dual_tolerance=",options.dual_tolerance,
        " zero_tolerance=",options.zero_tolerance)
    if !isnothing(data.native_numeric)
        native=data.native_numeric
        diagonal=diag(native.U)
        println("NATIVE_U min_abs_diagonal=",minimum(abs,diagonal),
            " max_abs_diagonal=",maximum(abs,diagonal),
            " finite_L=",all(isfinite,native.L.nzval),
            " finite_U=",all(isfinite,native.U.nzval))
    end
    flush(stdout)
end
include(joinpath(@__DIR__,"../../simplex-basis-cleanup-performance/reproduce/inspect-snapshot.jl"))
