using LinearAlgebra

BLAS.set_num_threads(1)
ENV["RUNTIME_AUDIT_ORIGINAL_COST"] = "1"
ENV["RUNTIME_TARGET_ITERATIONS"] = "50000"
ENV["RUNTIME_TIME_LIMIT"] = "900"
ENV["RUNTIME_TRACE_START"] = "0"
ENV["RUNTIME_TRACE_END"] = "0"
ENV["RUNTIME_CAPTURE_START"] = "0"
ENV["RUNTIME_SCAN_START"] = "0"

include("runtime_reduced_continuation.jl")
main()
