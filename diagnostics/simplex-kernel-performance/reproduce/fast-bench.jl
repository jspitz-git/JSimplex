label=first(ARGS)
run_runtime=length(ARGS)>1 && ARGS[2]=="runtime"
include("measure.jl")
include("solve-bench.jl")
for algorithm in ("dual","primal")
    empty!(ARGS)
    append!(ARGS,["/home/jspitz/mps/fast0507.mps",algorithm,"legacy","120","3",
        joinpath(@__DIR__,"../results",label*"-fast-"*algorithm*"-bench.toml")])
    main()
    measure("/home/jspitz/mps/fast0507.mps",algorithm,"10000","120",
        joinpath(@__DIR__,"../results",label*"-fast-"*algorithm*"-trace"))
end

if run_runtime
    measure("/home/jspitz/mps/runtime.mps","dual","1000000","600",
        joinpath(@__DIR__,"../results",label*"-runtime-dual"))
end
