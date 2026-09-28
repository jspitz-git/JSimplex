include(joinpath(@__DIR__, "capture.jl"))
length(ARGS)>=4 || error("Expected: input seconds output_prefix manager...")
input,seconds,prefix=ARGS[1:3]
mkpath(dirname(abspath(prefix)))
for manager in ARGS[4:end]
    output=prefix*"-"*manager*".toml"
    log=prefix*"-"*manager*".log"
    ispath(log) && error("Choose a fresh log path")
    println("Starting ",manager);flush(stdout)
    open(log,"w") do io
        redirect_stdout(io) do
            redirect_stderr(io) do
                with_logger(ConsoleLogger(io)) do
                    Base.invokelatest(capture_primal,[input,manager,seconds,output])
                end
            end
        end
    end
    report=TOML.parsefile(output)
    println(manager,": ",report["status"]," iterations=",report["iterations"],
        " refactorizations=",report["refactorizations"]," seconds=",report["seconds"])
    flush(stdout)
    GC.gc()
end
