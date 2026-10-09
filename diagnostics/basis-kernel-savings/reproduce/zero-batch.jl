# Verify total batch allocations without integer averaging. This is an
# allocation check only; use the repeated probes for elapsed-time estimates.
script=popfirst!(ARGS)
source=read(script,String)
@assert occursin("t.bytes÷count",source)
source=replace(source,"t.bytes÷count"=>"begin; @assert t.bytes == 0; 0; end", "1:11"=>"1:1")
include_string(Main,source,abspath(script))
