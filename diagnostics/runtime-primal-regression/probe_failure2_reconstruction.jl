# Separate FTRAN/BTRAN reconstruction outcomes from bound feasibility.
include(joinpath(@__DIR__, "diagnose_failure2.jl"))
include(joinpath(@__DIR__, "verify_basis_reconstruction.jl"))
using LinearAlgebra, Serialization, TOML

function probe(input, output)
    ispath(output) && error("Use a fresh output file")
    BLAS.set_num_threads(8)
    d = deserialize(input)
    ws = restore_reconstruction_workspace(d)
    @assert eltype(ws.primal) == Float64
    B = JS.basis_matrix(ws)
    rhs = JS._basis_primal_rhs(ws)
    basic = copy(ws.primal[ws.basis.basic_indices])
    dual = copy(ws.scratch.rho)
    stop = ()->false
    before = Failure2Diagnostics.quality(ws, basic, rhs)
    basic_ok = JS._native_cleanup_solve!(basic,ws,B,rhs,stop;local_reconstruction=true)
    after = Failure2Diagnostics.quality(ws, basic, rhs)
    dual_before = Failure2Diagnostics.quality(ws,dual,ws.costs[ws.basis.basic_indices];transposed=true)
    dual_ok = JS._native_cleanup_solve!(dual,ws,B,ws.costs[ws.basis.basic_indices],stop;
        transposed=true,local_reconstruction=true)
    dual_after = Failure2Diagnostics.quality(ws,dual,ws.costs[ws.basis.basic_indices];transposed=true)
    original_violations = Failure2Diagnostics.violations(ws)
    ws.primal[ws.basis.basic_indices] .= basic
    trial_violations = Failure2Diagnostics.violations(ws)
    combined = restore_reconstruction_workspace(d)
    combined_ok = JS._try_native_cleanup_recompute!(combined,stop)
    report=Dict("blas_threads"=>BLAS.get_num_threads(),"arithmetic_type"=>string(eltype(basic)),
        "primal_tolerance"=>d.options.primal_tolerance,"solve_tolerance"=>d.policy.solve_tolerance,
        "primal_reconstruction_accepted"=>basic_ok,"transpose_reconstruction_accepted"=>dual_ok,
        "primal_before"=>before,"primal_after"=>after,"transpose_before"=>dual_before,
        "transpose_after"=>dual_after,"original_violations"=>original_violations,
        "primal_trial_violations"=>trial_violations,"combined_accepted"=>combined_ok,
        "combined_violations"=>Failure2Diagnostics.violations(combined),
        "options_unchanged"=>combined.options === d.options,
        "policy_unchanged"=>combined.progress.numerical_policy === d.policy,
        "basis_unchanged"=>combined.basis.basic_indices == d.basis.basic_indices)
    open(output,"w") do io
        TOML.print(io,report;sorted=true)
    end
    println("Primal reconstructed: ",basic_ok,"; transpose reconstructed: ",dual_ok,
        "; combined: ",combined_ok,"; violations: ",length(report["combined_violations"]))
    @assert report["options_unchanged"] && report["policy_unchanged"] && report["basis_unchanged"]
end

if abspath(PROGRAM_FILE)==@__FILE__
    length(ARGS)==2 || error("Expected: before-reconstruction.bin output.toml")
    probe(ARGS...)
end
