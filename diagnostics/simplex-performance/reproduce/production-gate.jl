using JSimplex, Test
const gate_root = normpath(joinpath(@__DIR__,"..",".."))
function gate_include(path)
    println("TEST_FILE_BEGIN ",path);flush(stdout)
    started=time_ns()
    result=Base.include(Main,joinpath(gate_root,"test",path))
    println("TEST_FILE_END ",path," seconds=",(time_ns()-started)/1e9);flush(stdout)
    return result
end
function instrument_includes(expression)
    expression isa Expr || return expression
    if expression.head==:call && expression.args[1]==:include && length(expression.args)==2 && expression.args[2] isa String
        return Expr(:call,:gate_include,expression.args[2])
    end
    return Expr(expression.head,map(instrument_includes,expression.args)...)
end
Base.include(instrument_includes,Main,joinpath(gate_root,"test/runtests.jl"))
