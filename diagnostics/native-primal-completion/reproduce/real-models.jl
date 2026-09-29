include(joinpath(@__DIR__, "../../simplex-kernel-performance/reproduce/measure.jl"))

outdir = abspath(first(ARGS))
mkpath(outdir)
for (name, algorithm, seconds) in (("fast0507", "primal", "300"), ("runtime", "dual", "600"))
    measure("/home/jspitz/mps/" * name * ".mps", algorithm, "1000000", seconds,
            joinpath(outdir, name * "-" * algorithm))
end
