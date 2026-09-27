using Pkg, TOML
measured = @timed Pkg.precompile()
open(ARGS[1],"w") do io
    TOML.print(io,Dict("seconds"=>measured.time,"julia"=>string(VERSION),
        "image_threads"=>get(ENV,"JULIA_IMAGE_THREADS",""),
        "precompile_workers"=>get(ENV,"JULIA_NUM_PRECOMPILE_TASKS","")))
end
