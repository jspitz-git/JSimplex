# Residual-only replay. Does not advance, refactorize, or repair the saved basis.
include(joinpath(@__DIR__, "capture_basis_failure.jl"))
using Serialization
length(ARGS)==2 || error("Expected: snapshot.basis-failure.bin output_prefix")
input,prefix=ARGS
for suffix in (".replay.toml",".replay-environment.toml")
    ispath(prefix*suffix) && error("Use a fresh output prefix: "*prefix)
end
mkpath(dirname(abspath(prefix)))
RuntimePrimalCapture.write_report(prefix*".replay-environment.toml",RuntimePrimalCapture.environment(input))
data=deserialize(input)
report=RuntimeBasisFailure.summarize(data)
RuntimePrimalCapture.write_report(prefix*".replay.toml",report)
println("Primal reliable: ",report["primal"]["reliable"],
    "; transpose reliable: ",report["transpose"]["reliable"])
