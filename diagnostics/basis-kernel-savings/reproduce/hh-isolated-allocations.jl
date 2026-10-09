# Isolate kernel allocations from heterogeneous-arm dispatch in the HH harness.
# The timed batch and its count are unchanged; dispatch occurs before @timed.
script = popfirst!(ARGS)
source = read(script, String)
helper = """
function measure_batch(y,f,rhs,updates::U,n::Int,mode) where {U}
    @timed batch(y,f,rhs,updates,n,mode)
end
"""
@assert occursin("t=@timed batch(y,f,rhs,alternatives[i],count,mode)", source)
source = replace(source,
    "function main(out)" => helper * "\nfunction main(out)",
    "t=@timed batch(y,f,rhs,alternatives[i],count,mode)" =>
        "t=measure_batch(y,f,rhs,alternatives[i],count,mode)",
    "t.bytes÷count" => "begin; @assert t.bytes == 0; t.bytes; end",
    "\"index_count\"=>index_count" => "\"batch_count\"=>count,\"index_count\"=>index_count")
include_string(Main, source, abspath(script))
