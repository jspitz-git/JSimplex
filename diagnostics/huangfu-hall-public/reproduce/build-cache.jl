using Pkg, TOML
# Apply the GC hint to the compiler worker as well as the coordinating process.
# This changes memory collection, not native-code optimization or cache flags.
Pkg.resolve()
measured = @timed Pkg.precompile(["JSimplex"]; strict=true,
    configs=(`--heap-size-hint=2G` => Base.CacheFlags()))
cached = Base.isprecompiled(Base.identify_package("JSimplex"); ignore_loaded=true)
@assert cached "The compiler did not produce a reusable JSimplex cache"
open(ARGS[1], "w") do io
    TOML.print(io, Dict("seconds"=>measured.time, "julia"=>string(VERSION),
        "cached"=>cached, "worker_heap_hint"=>"2G",
        "debug_level"=>Int(Base.JLOptions().debug_level), "opt_level"=>Int(Base.JLOptions().opt_level),
        "precompile_workers"=>get(ENV, "JULIA_NUM_PRECOMPILE_TASKS", ""),
        "image_threads"=>get(ENV, "JULIA_IMAGE_THREADS", "")))
end
