# Diagnostic follow-up: preserve unrounded total bytes and batch size for HH.
# The solve implementation and eleven alternating rounds are unchanged.
script = popfirst!(ARGS)
source = read(script, String)
@assert occursin("t.bytes÷count", source)
source = replace(source, "t.bytes÷count" => "t.bytes",
    "\"index_count\"=>index_count" => "\"batch_count\"=>count,\"index_count\"=>index_count")
include_string(Main, source, abspath(script))
